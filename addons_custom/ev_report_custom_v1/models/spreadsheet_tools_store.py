from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import psycopg2

class SpreadsheetToolsStore(models.Model):
    _name = 'spreadsheet.tools.store'
    _description = 'Spreadsheet Tools Store'
    _auto = False

    def get_data(self, **kwargs):
        rows = self._get_data_query(**kwargs)

        total_original = 0
        total_start_value = 0
        total_depreciated_value = 0
        total_residual_value = 0
        total_value_in_period = 0

        for row in rows:
            total_original += row['nguyengia'] or 0
            total_start_value += row['gtbatdaukh'] or 0
            total_depreciated_value += row['gtdakh'] or 0
            total_residual_value += row['gtconlai'] or 0
            total_value_in_period += row['gtkhtrongky'] or 0

        summary = {
            'total_original': total_original,
            'total_start_value': total_start_value,
            'total_depreciated_value': total_depreciated_value,
            'total_residual_value': total_residual_value,
            'total_value_in_period': total_value_in_period,
        }

        return {'data': rows, 'summary': summary}

    def _get_data_query(self, **kwargs):
        date_from = kwargs.get('from_date').strftime('%d/%m/%Y')
        date_to = kwargs.get('to_date').strftime('%d/%m/%Y')

        try:
            host = self.env['ir.config_parameter'].sudo().get_param('slave_db_host')
            database = self.env['ir.config_parameter'].sudo().get_param('slave_db_name')
            user = self.env['ir.config_parameter'].sudo().get_param('slave_db_user')
            password = self.env['ir.config_parameter'].sudo().get_param('slave_db_password')
            port = self.env['ir.config_parameter'].sudo().get_param('slave_db_port')
            conn = psycopg2.connect(host=host, database=database, user=user, password=password,
                                    port=port)
            # create a cursor
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            sql = """
                select tents, mats, to_char(ngaytinhkh,'dd/mm/yyyy') ngaytinhkh, sokyhk,
                    case
                        when trangthai = 'open' then 'Đang chạy'
                        when trangthai = 'close' then 'Đã đóng'
                        when trangthai = 'draft' then 'Dự thảo'
                        else null end as  trangthai, nguyengia, gtbatdaukh,
                    case when gtdakh is not null then gtdakh else 0 end as  gtdakh,
                    case when gtdakh is not null then gtbatdaukh - gtdakh
                    else gtbatdaukh end as gtconlai,
                    sum(gtkhtrongky)      gtkhtrongky
                from (SELECT b.name tents, b.x_code mats, b.id id,
                        to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),'dd/mm/yyyy') ngaytinhkh,
                        b.method_number sokyhk, b.original_value nguyengia,
                        case
                            when b.already_depreciated_amount_import is not null
                            then b.original_value - b.already_depreciated_amount_import
                        else b.original_value end as gtbatdaukh,
                        (select sum(am.amount_total)
                        from account_move am
                        join account_asset aa on am.asset_id = aa.id
                        where aa.id = b.id
                        and am.state = 'posted'
                        and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                            to_date(%s, 'dd/mm/yyyy')) as gtdakh,
                        sum(a.amount_total) gtkhtrongky, 0 as gtconlai,
                        b.state trangthai
                    from account_move a
                    join account_asset b on b.id = a.asset_id
                    WHERE b.x_asset_type in ('tools', 'expenses')
                    and a.state = 'posted'
                    and b.state in ('open', 'close')
                    and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
                    and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
                    group by b.id, tents, mats, nguyengia, gtbatdaukh, gtdakh, gtconlai, ngaytinhkh, trangthai
    
                    union all
    
                    SELECT b.name tents, b.x_code mats, b.id id,
                        to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'),'dd/mm/yyyy') ngaytinhkh,
                        b.method_number sokyhk, b.original_value nguyengia,
                        case
                            when b.already_depreciated_amount_import is not null
                            then b.original_value - b.already_depreciated_amount_import
                        else b.original_value end as gtbatdaukh,
                        (select sum(am.amount_total)
                        from account_move am
                        join account_asset aa on am.asset_id = aa.id
                        where aa.id = b.id
                        and am.state = 'posted'
                        and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                            to_date(%s, 'dd/mm/yyyy')) as gtdakh,
                        0 gtkhtrongky, 0 gtconlai, b.state trangthai
                    from account_asset b
                    left join account_move a on b.id = a.asset_id
                    join account_account c on c.id = b.account_asset_id
                    where b.x_asset_type in ('tools', 'expenses')
                    and b.state != 'model'
        --          and b.original_value = 0
                    and to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
                    to_date(%s, 'dd/mm/yyyy')
                    and to_date(to_char(b.first_depreciation_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                    to_date(%s, 'dd/mm/yyyy')
                    group by b.id, tents, mats, nguyengia, ngaytinhkh, gtdakh, sokyhk, gtbatdaukh, trangthai
                ) as asset_tracking
            group by id, tents, mats, nguyengia, gtbatdaukh, ngaytinhkh, sokyhk, gtdakh, trangthai
            """

            params = (date_to, date_from, date_to, date_to, date_from, date_to)
            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)

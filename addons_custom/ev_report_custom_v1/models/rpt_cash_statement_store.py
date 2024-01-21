from odoo import api, fields, models
from odoo.exceptions import ValidationError
import psycopg2

class EndOfDayAuditStore(models.Model):
    _name = "rpt.cash.statement.store"
    _description = "Báo Cáo Kiểm Quỹ cuối ngày"

    def get_data(self, **kwargs):
        to_date = kwargs.get('to_date').strftime('%d/%m/%Y')
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

            sql = '''
            select ps.code                                                              macuahang,
            ps.name                                                                     tencuahang,
            (case When sr.name is not null then sr.name else '' end ) as                tenvung,
            to_char(start_at + INTERVAL '7 hours', 'dd/mm/yyyy HH24:mi:ss')              start_at,
            COALESCE(to_char(stop_at + INTERVAL '7 hours', 'dd/mm/yyyy HH24:mi:ss'), '') stop_at,
            p.x_money_total_cash_app                              doanhthutrenpm,
            p.x_amount_total_cash_iput                            quycuoingay,
            p.x_amount_total_cash_iput - p.x_money_total_cash_app chenhlech,
            (case WHEN p.x_reason_money_difference is not null then p.x_reason_money_difference else '' end) as lydo
            from pos_shop ps
            left join stock_warehouse sw on ps.warehouse_id = sw.id
            left join stock_region sr on sw.x_stock_region_id = sr.id
            right join pos_session p on ps.id = p.x_pos_shop_id
            where to_date(to_char(p.start_at + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') = to_date(%s, 'dd/mm/yyyy')
            '''
            params = (to_date, )
            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)
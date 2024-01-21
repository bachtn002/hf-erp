from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
import psycopg2


class PreTaxRevenueReportStore(models.Model):
    _name = "pre.tax.revenue.report.store"
    _description = "Pre Tax Revenue Report Store"
    _auto = False

    def get_data(self, **kwargs):
        rows = self._get_data_query(**kwargs)

        total_revenue = 0
        total_revenue_refund = 0
        total_cost = 0
        total_profit = 0

        for row in rows:
            total_revenue += row['revenue'] or 0
            total_revenue_refund += row['revenue_refund'] or 0
            total_cost += row['giavon'] or 0
            total_profit += row['loinhuan'] or 0

        summary = {
            'total_revenue': total_revenue,
            'total_revenue_refund': total_revenue_refund,
            'total_cost': total_cost,
            'total_profit': total_profit,
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
            select shop_name, -sum(revenue) revenue, 
                sum(revenue_refund) revenue_refund, sum(giavon) giavon,
                -sum(revenue) - sum(revenue_refund) - sum(giavon) as loinhuan
            from (
                select ps.name        as shop_name,
                    sum(a.balance) as revenue,
                    0              as revenue_refund,
                    0                 giavon
                from account_move_line a
                join account_move b on a.move_id = b.id
                join account_account c on c.id = a.account_id
                join pos_session pss on pss.move_id = b.id
                join pos_shop ps on ps.id = pss.x_pos_shop_id
                where c.code = '5111'
                and b.state = 'posted'
                and a.date >= to_date(%s, 'dd-mm-yyyy')
                and a.date <= to_date(%s, 'dd-mm-yyyy')
                group by shop_name
    
                union all
    
                select ps.name      as shop_name,
                    0            as revenue,
                    sum(a.balance) as revenue_refund,
                    0               giavon
                from account_move_line a
                join account_move b on a.move_id = b.id
                join account_account c on c.id = a.account_id
                join pos_session pss on pss.move_id = b.id
                join pos_shop ps on ps.id = pss.x_pos_shop_id
                where c.code like concat('521', '%%')
                and b.state = 'posted'
                and a.date >= to_date(%s, 'dd-mm-yyyy')
                and a.date <= to_date(%s, 'dd-mm-yyyy')
                group by shop_name
    
                union all
    
                select f.name shop_name, 0 revenue, 0 revenue_refund, 
                    sum(a.debit)- sum(a.credit) as giavon
                from account_move_line a
                join account_move b on b.id = a.move_id
                join stock_move c on c.id = b.stock_move_id
                join stock_picking d on d.id = c.picking_id
                left join pos_session e on e.id = d.pos_session_id
                left join pos_shop f on f.id = e.x_pos_shop_id
                join account_account g on g.id = a.account_id
                where g.code = '632'
                and b.state = 'posted'
                and a.date >= to_date(%s, 'dd-mm-yyyy')
                and a.date <= to_date(%s, 'dd-mm-yyyy')
                group by shop_name
                ) as t
            group by shop_name
            """

            params = (date_from, date_to, date_from, date_to, date_from, date_to,)
            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)
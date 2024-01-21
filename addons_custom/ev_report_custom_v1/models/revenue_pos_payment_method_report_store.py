from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import psycopg2

class RevenuePosPaymentMethodReportStore(models.Model):
    _name = 'revenue.pos.payment.method.report.store'
    _description = 'Revenue Pos Payment Method Store'
    _auto = False

    def get_data(self, **kwargs):
        pos_shop_ids = kwargs.get('pos_shop_ids')
        date_from = kwargs.get('date_from')
        date_to = kwargs.get('date_to')
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
            select to_char(pp.payment_date + INTERVAL '7 hours', 'dd/mm/yyyy') date_group,
                    to_char(pp.payment_date + INTERVAL '7 hours', 'dd/mm/yyyy') to_date,
                    ps.code                                                                            code_shop,
                    ps.name                                                                            name_shop,
                    case when ppm.is_cash_count = True 
                    THEN 'Quỹ tiền mặt' 
                    ELSE ppm.name END           payment_method,
                    sum(pp.amount)
            from pos_payment pp
            left join pos_shop ps on pp.x_pos_shop_id = ps.id
            left join pos_payment_method ppm on pp.payment_method_id = ppm.id
            where (ps.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
            AND to_date(to_char(pp.payment_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
            AND to_date(to_char(pp.payment_date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
    
            group by ps.code, ps.name, ppm.name, pp.payment_date, ppm.is_cash_count
            order by pp.payment_date;
            """

            params = (pos_shop_ids, pos_shop_ids, date_from, date_to)

            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)

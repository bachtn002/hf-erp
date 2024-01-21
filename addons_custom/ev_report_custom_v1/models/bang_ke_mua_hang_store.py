from odoo import api, fields, models
from odoo.exceptions import ValidationError
import psycopg2

class BangKeMuaHangStore(models.Model):
    _name = "bang.ke.mua.hang.store"
    _description = "Bảng Kê mua hàng"

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
                SELECT to_char(sr.date,'dd/mm/yyyy') date_order, sw.name kho, pc.name nhomhh, pp.default_code msp, pt.name tensp,
                       uu.name dvt, srl.qty_buy, srl.price_unit gia, srl.qty_buy * srl.price_unit thanhtien,
                       (case WHEN rp.ref is not null then rp.ref else '' end) as ma_ncc
                FROM supply_request sr
                    left join supply_request_line srl on sr.id = srl.supply_request_id
                    left join stock_warehouse sw on srl.warehouse_dest_id = sw.id
                    left join product_category pc on srl.categ_id = pc.id
                    left join product_product pp on srl.product_id = pp.id
                    left join product_template pt on pp.product_tmpl_id = pt.id
                    left join uom_uom uu on srl.uom_id = uu.id
                    left join res_partner rp on srl.partner_id = rp.id
                WHERE to_date(to_char(sr.date, 'dd/mm/yyyy'), 'dd/mm/yyyy') = to_date( %s, 'dd/mm/yyyy')
            '''
            params = [to_date]
            cur.execute(sql, tuple(params))
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)

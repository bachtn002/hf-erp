from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import psycopg2


class BangKeChiTietBanHangStore(models.Model):
    _name = "bang.ke.chi.tiet.ban.hang.store"
    _description = "Bảng kê chi tiết bán hàng"

    def get_data(self, **kwargs):
        from_date = kwargs.get('from_date').strftime('%d/%m/%Y')
        to_date = kwargs.get('to_date').strftime('%d/%m/%Y')

        pos_shop_ids = self.env.user.x_pos_shop_ids
        if self.env.user.x_view_all_shop:
            pos_shop_ids = ''
        else:
            if pos_shop_ids:
                pos_shop_ids = ','.join([str(idd) for idd in pos_shop_ids.ids])
            else:
                raise UserError(_('User not posh shop'))

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
                select code_shop, shop_name, order_name, date_order, partner, customer, default_code, full_product_name, dvt,
                    category_name, qty, price_unit, 
                    ROUND(tienVAT::numeric, 0)                                          tienVAT,
                    ROUND(khuyenmai::numeric, 0)                                        khuyenmai,
                    ROUND(discount::numeric, 0)                                         discount, 
                    ROUND(doanhthuthuc::numeric, 0)                                     doanhthuthuc,
                    ROUND((doanhthuthuc/(1+VAT))::numeric, 0)						    tt_chua_vat,
                    doanhthuthuc - ROUND((doanhthuthuc/(1+VAT))::numeric, 0)            tienVATthuc,
                    ROUND((ROUND((doanhthuthuc/(1+VAT))::numeric, 0)/qty)::numeric, 2)    dd_chua_vat, '' tongthanhtoan,
                    promotion_name, user_name
		        from 
                (select ps.code                                                                  code_shop,
                       ps.name                                                                  shop_name,
                       po.name                                                                  order_name,
                       to_char(po.date_order + INTERVAL '7 hours', 'dd/mm/yyyy')                date_order,
                       CAST(po.partner_id AS varchar)                                           partner,
                       rp.name                                                                  customer,
                       pp.default_code                                                          default_code,
                       pol.full_product_name                                                    full_product_name,
                       uu.name                                                                  dvt,
                       pc.name                                                                  category_name,
                       pol.qty                                                                  qty,
                       pol.price_unit                                                           price_unit,
                       at.amount / 100                                                          VAT,
                       pol.x_is_price_promotion                                                 khuyenmai,
                       pol.amount_promotion_loyalty + pol.amount_promotion_total                discount,
                       pol.discount                                                             chietkhau,
                       pol.x_product_promotion                                                  promotion_name,
                       rpt.name                                                                 user_name,
                       
                       pol.qty * pol.price_unit * (1 - pol.discount / 100)                      tienVAT,
                       CASE
                            WHEN pol.qty < 0 THEN (pol.qty * pol.price_unit * (1 - pol.discount / 100)) + (pol.amount_promotion_loyalty + pol.amount_promotion_total) + pol.x_is_price_promotion
                            ELSE (pol.qty * pol.price_unit * (1 - pol.discount / 100)) - (pol.amount_promotion_loyalty + pol.amount_promotion_total) - pol.x_is_price_promotion 
                            END as                     											doanhthuthuc
                       
                from pos_order_line pol
                         left join pos_order po on pol.order_id = po.id
                --          left join account_tax_pos_order_line_rel atpolr on pol.id = atpolr.pos_order_line_id
                         left join pos_shop ps on po.x_pos_shop_id = ps.id
                         left join res_partner rp on po.partner_id = rp.id
                         left join product_product pp on pol.product_id = pp.id
                         left join product_template pt on pp.product_tmpl_id = pt.id
                         join uom_uom uu on uu.id = pt.uom_id
                         join product_taxes_rel ptr on ptr.prod_id = pt.id
                         left join account_tax at on ptr.tax_id = at.id
                         left join product_category pc on pt.categ_id = pc.id
                         left join res_users ru on po.user_id = ru.id
                         left join res_partner rpt on ru.partner_id = rpt.id
                         left join pos_promotion pprt on pol.promotion_id = pprt.id
                where (ps.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '')
                    AND pol.price_unit >= 0
                    AND pol.is_combo_line = False
                    AND to_date(to_char(po.date_order + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
                    AND to_date(to_char(po.date_order + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
                order by po.date_order) as l1
            '''
            params = (pos_shop_ids, pos_shop_ids, from_date,to_date)
            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)
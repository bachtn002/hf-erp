# -*- coding: utf-8 -*-
import odoo.tools.config as config

from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError


class StockQuantCurrent(models.TransientModel):
    _name = 'stock.quant.current'

    name = fields.Char(string="Name", default="Báo cáo tồn kho hiện tại")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    line_ids = fields.One2many('stock.quant.current.line', 'stock_quant_current_id', string='Products')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    product_ids = fields.Many2many('product.product', 'stock_current_product', 'stock_current_id', 'product_id',
                                   string='Product')

    @api.onchange('user_id')
    def set_domain_for_warehouse(self):
        if self.user_id:
            if self.user_id.has_group('ev_stock_access_right.group_stock_access_all'):
                return {'domain': {'warehouse_id': [(1, '=', 1)]}}
            else:
                return {'domain': {'warehouse_id': [('id', 'in', self.user_id.warehouse_ids.ids)]}}

    def action_generate(self):
        try:
            self.line_ids.unlink()
            location_id = self.warehouse_id.lot_stock_id
            pos_shop = self.env['pos.shop'].search([('warehouse_id', '=', self.warehouse_id.id)])
            company_id = self.env.user.company_id
            product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
            stock_quant_current = self._get_stock_quant_current(company_id.id, pos_shop.id, location_id.id, product_ids)
            vals = []
            if stock_quant_current:
                for record in stock_quant_current:
                    val = {
                        'product_id': record[0],
                        'uom_id': record[1],
                        'quantity': record[2],
                        'stock_quant_current_id': self.id,
                    }
                    vals.append((0, 0, val))
                self.line_ids = vals
        except Exception as e:
            raise ValidationError(e)

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/ev_stock_report_birt.stock_quant_current_xlsx/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def _get_stock_quant_current(self, company_id, pos_shop_id, location_id, product_ids):
        try:
            query = """
                    SELECT product_id, uom_id, sum(quantity)
                    from (
                             SELECT pp.id as product_id, uu.id as uom_id, - sum(pol.qty) as quantity
                             from pos_order_line pol
                                      left join pos_order po on po.id = pol.order_id
                                      left join pos_shop ps on ps.id = po.x_pos_shop_id
                                      left join product_product pp on pp.id = pol.product_id
                                      left join product_template ptl on ptl.id = pp.product_tmpl_id
                                      left join uom_uom uu on uu.id = ptl.uom_id
                                      join pos_session pss on pss.id = po.session_id
                             where pol.company_id = %s
                               and ps.id = %s
                               and po.state = 'paid'
                               and ptl.active = True
                               and ptl.type = 'product'
                               and pss.state != 'closed'
                               and (pp.id in (%s) or '%s' = '0')
                             group by pp.id, uu.id
                             union all
                             SELECT pp.id as product_id, uu.id as uom_id, sum(sq.quantity) as quantity
                             from stock_quant sq
                                      left join product_product pp on pp.id = sq.product_id
                                      left join product_template ptl on ptl.id = pp.product_tmpl_id
                                      left join uom_uom uu on uu.id = ptl.uom_id
                             where sq.company_id = % s
                               and sq.location_id = % s
                               and ptl.active = True
                               and ptl.type = 'product'
                               and (pp.id in (%s) or '%s' = '0')
                             group by pp.id, uu.id
                         ) as stock_quant
                    where quantity != 0
                    group by product_id, uom_id
                    order by product_id desc
            """ % (company_id, pos_shop_id, product_ids, product_ids, company_id, location_id, product_ids, product_ids)
            self._cr.execute(query)
            values = self._cr.fetchall()
            return values
        except Exception as e:
            raise ValidationError(e)

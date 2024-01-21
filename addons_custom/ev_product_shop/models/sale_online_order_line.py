from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOnlineOrderLine(models.Model):
    _inherit = 'sale.online.order.line'

    @api.onchange('product_id')
    def _onchange_domain_product_id(self):
        try:
            if self.sale_online_id.pos_config_id:
                pos_shop = self.sale_online_id.pos_config_id.x_pos_shop_id
                if self.product_id:
                    if self.product_id.x_is_combo == True:
                        for detail in self.product_id.x_product_combo_ids:
                            if detail.product_ids.product_tmpl_id.id not in pos_shop.product_ids.ids:
                                raise UserError(_('Detail in combo not config in Shop!, ' + detail.product_ids.name))
                domain = ['|', '&', '&','&',
                          ('id', 'in', pos_shop.product_ids.ids),
                          ('available_in_pos', '=', True),
                          ('active', '=', True),
                          ('sale_ok', '=', True),
                          '&',
                          ('type', '=', 'service'),
                          ('active', '=', True),
                          ('sale_ok', '=', True),
                          ('available_in_pos', '=', True)
                          ]
                return {'domain': {'product_id': domain}}
            else:
                raise UserError(_('Please choose a POS!'))
        except Exception as e:
            raise ValidationError(e)

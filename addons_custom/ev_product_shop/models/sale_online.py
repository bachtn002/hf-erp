from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOnline(models.Model):
    _inherit = 'sale.online'

    def send_sale_request(self):
        try:
            pos_shop = self.pos_config_id.x_pos_shop_id
            for line in self.order_line_ids:
                if line.product_id.type != 'service':
                    if line.product_id not in pos_shop.product_ids:
                        raise UserError(_('Product not in shop, ' + line.product_id.name))
                if line.product_id.x_is_combo == True:
                    for detail in line.product_id.x_product_combo_ids:
                        if detail.product_ids.product_tmpl_id.id not in pos_shop.product_ids.ids:
                            raise UserError(_('Detail in combo not config in Shop!, ' + detail.product_ids.name))
            return super(SaleOnline, self).send_sale_request()
        except Exception as e:
            raise ValidationError(e)

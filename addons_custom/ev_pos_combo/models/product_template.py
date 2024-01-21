from odoo import fields, models, api


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    x_is_combo = fields.Boolean(string='Is Combo', track_visibility='onchange')
    x_product_combo_ids = fields.One2many('product.combo', 'product_tmpl_id', string='Combos')
    x_product_old_id = fields.Integer('Product Old Id')

    @api.onchange('x_is_combo')
    def _onchange_x_is_combo(self):
        if self.x_is_combo:
            self.available_in_pos = self.x_is_combo
            self.type = 'service'
            # self.x_supply_type = False

    @api.model
    def create(self, values):
        # if values['x_is_combo']:
        #     values['type'] = 'service'
        res = super(ProductTemplateInherit, self).create(values)
        if res.x_is_combo:
            if res.x_product_combo_ids:
                standard_price = 0.0
                for product_combo in res.x_product_combo_ids:
                    for product in product_combo.product_ids:
                        standard_price += product.standard_price * product_combo.no_of_items
                        # if combo available in pos then product in combo detail also need to available in pos
                        # and belong to the sale shops
                        product.sale_ok = res.sale_ok
                        product.available_in_pos = res.available_in_pos
                        product.x_pos_shop_ids |= res.x_pos_shop_ids
                res.standard_price = standard_price
        return res

    def write(self, values):
        # if values['x_is_combo']:
        #     values['type'] = 'service'
        res = super(ProductTemplateInherit, self).write(values)
        for item in self:
            if item.x_is_combo:
                if item.x_product_combo_ids:
                    standard_price = 0.0
                    for product_combo in item.x_product_combo_ids:
                        for product in product_combo.product_ids:
                            standard_price += product.standard_price * product_combo.no_of_items
                            # if combo available in pos then product in combo detail also need to available in pos
                            # and belong to the sale shops
                            product.sale_ok = item.sale_ok
                            product.available_in_pos = item.available_in_pos
                            product.x_pos_shop_ids |= item.x_pos_shop_ids
                    sql = """
                        UPDATE ir_property a SET value_float = %s
                        FROM product_product b, product_template c
                        WHERE
                        a.name = 'standard_price'
                        and a.res_id = 'product.product,' || b.id
                        and b.product_tmpl_id = c.id
                        and c.id = %s;
                    """
                    self._cr.execute(sql % (standard_price, item.id))
        return res

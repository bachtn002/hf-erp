# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCombo(models.Model):
    _name = 'product.combo'
    _description = 'Product combo'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    require = fields.Boolean(string="Required", Help="Don't select it if you want to make it optional", default=True)
    require_one = fields.Boolean(string='Required one')
    pos_category_id = fields.Many2one('pos.category', string="Categories")
    # product_ids = fields.Many2many('product.product', string="Products")
    product_ids = fields.Many2one('product.product', string="Products")
    no_of_items = fields.Float(string="No. of Items", digits=(1, 3))

    @api.onchange('require', 'pos_category_id')
    def onchange_require(self):
        if self.require:
            self.pos_category_id = False
            self.require_one = False
            self.product_ids = [(5,)]
        if self.pos_category_id:
            self.product_ids = [(5,)]

    @api.onchange('pos_category_id')
    def _onchange_category_id(self):
        domain = [('x_is_combo', '=', False), ('available_in_pos', '=', True)]
        if self.pos_category_id:
            domain.append(('pos_categ_id', '=', self.pos_category_id.id))
        return {'domain': {
            'product_ids': domain
        }}
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductPriceHistory(models.Model):
    """ Keep track of the ``product.template`` standard prices as they are changed. """
    _name = 'product.price.history'
    _rec_name = 'datetime'
    _order = 'datetime desc'
    _description = 'Product Price List History'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.company.id)

    company_id = fields.Many2one('res.company', string='Company',
        default=_get_default_company_id, required=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', 'Template', ondelete='cascade')
    inventory_valuation_group_id = fields.Many2one('inventory.valuation.group', 'Inventory Valuation Group')
    datetime = fields.Datetime('Date', default=fields.Datetime.now)
    cost = fields.Float('Cost')
    cost_price_period_line_id = fields.Many2one('cost.price.period.line', 'Cost price period line')

    @api.model
    def create(self, vals):
        res = super(ProductPriceHistory, self).create(vals)
        if res.product_tmpl_id and not res.product_id:
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', res.product_tmpl_id.id)], limit=1)
            res.product_id = product_id.id
        elif res.product_id and not res.product_tmpl_id:
            res.product_tmpl_id = res.product_id.product_tmpl_id.id
        return res


class ProductPrice(models.Model):
    _name = 'product.price'
    _description = 'Product Price List'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.company.id)

    company_id = fields.Many2one('res.company', string='Company',
        default=_get_default_company_id, required=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', 'Template', ondelete='cascade')
    inventory_valuation_group_id = fields.Many2one('inventory.valuation.group', 'Inventory Valuation Group')
    cost = fields.Float('Cost')

    @api.model
    def create(self, vals):
        res = super(ProductPrice, self).create(vals)
        if res.product_tmpl_id and not res.product_id:
            product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', res.product_tmpl_id.id)], limit=1)
            res.product_id = product_id.id
        elif res.product_id and not res.product_tmpl_id:
            res.product_tmpl_id = res.product_id.product_tmpl_id.id
        return res

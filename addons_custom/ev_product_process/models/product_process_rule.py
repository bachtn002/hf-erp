# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError, ValidationError


class ProductProcessRule(models.Model):
    _name = "product.process.rule"

    @api.depends('to_rule_ids.percent')
    def _amount_total_percent(self):
        for order in self:
            total_percent = 0.0
            for line in order.to_rule_ids:
                total_percent += line.percent
            order.update({
                'total_percent': total_percent,
            })

    name = fields.Char('Name')
    active = fields.Boolean(sring='Active', default=True, track_visibility='onchange')
    from_rule_ids = fields.One2many('product.process.rule.line','from_rule_id', string="From Rule line")
    to_rule_ids = fields.One2many('product.process.rule.line','to_rule_id', string="To Rule line")
    note = fields.Text('Note')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    total_percent = fields.Float('Total percent', store=True, compute='_amount_total_percent')

    @api.model
    def create(self, vals):
        if vals.get('to_rule_ids'):
            total_percent = 0.0
            for rule in vals.get('to_rule_ids'):
                if rule[2] != False:
                    total_percent += rule[2]['percent']
            if total_percent != 100:
                    raise UserError(_("Total percent must be equal to 100!"))
        return super(ProductProcessRule, self).create(vals)

    def write(self, vals):
        res = super(ProductProcessRule, self).write(vals)
        if 'to_rule_ids' in vals:
            total_percent = 0.0
            for rule in vals['to_rule_ids']:
                line = self.env['product.process.rule.line'].search([('id','=',rule[1])], limit=1)
                if line:
                    total_percent += line.percent
            if total_percent != 100:
                raise UserError(_("Total percent must be equal to 100!"))
        return res


class ProductProcessRuleLine(models.Model):
    _name = "product.process.rule.line"

    from_rule_id = fields.Many2one('product.process.rule',string='From Rule')
    to_rule_id = fields.Many2one('product.process.rule',string='To Rule')
    product_id = fields.Many2one('product.product', string="Product", domain=[('type', '=', 'product')])
    uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string="Uom")
    qty = fields.Float(string="Quantity", default=1, digits='Product Unit of Measure')
    percent = fields.Float("Standard Price Percent")
    error_percent = fields.Float("Balance Percent")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id or self.product_id.uom_po_id.id



# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError, ValidationError


class ProductProcessLine(models.Model):
    _name = "product.process.line"
    _order = 'create_date desc'

    name = fields.Char('Name')
    process_id = fields.Many2one('product.process', "The Process")
    rule_id = fields.Many2one('product.process.rule', 'Rule')
    from_detail_ids = fields.One2many('product.process.detail', 'from_process_id', "From Products")
    to_detail_ids = fields.One2many('product.process.detail', 'to_process_id', "To Products")
    note = fields.Text("Note")
    picking_out_id = fields.Many2one('stock.picking', 'Picking Out')
    picking_in_id = fields.Many2one('stock.picking', 'Picking In')

    @api.onchange('rule_id')
    def _onchange_detail(self):
        if self.rule_id:
            self.name = self.rule_id.name
            tmp = []
            for line in self.rule_id.from_rule_ids:
                tmp.append((0, 0, {
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'qty': line.qty,
                    'origin_qty': line.qty,
                    'qty_change': line.qty,
                }))
            self.from_detail_ids = False
            self.from_detail_ids = tmp
            # khi tạo mới không lưu qty_change phải thêm vòng for để tạo giá trị qty_change
            for from_detail_id in self.from_detail_ids:
                from_detail_id.qty_change = from_detail_id.qty
            tmp = []
            for line in self.rule_id.to_rule_ids:
                tmp.append((0, 0, {
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'qty': line.qty,
                    'origin_qty': line.qty,
                    'percent': line.percent,
                    'error_percent': line.error_percent,
                }))
            self.to_detail_ids = False
            self.to_detail_ids = tmp

    @api.onchange('from_detail_ids')
    def _onchange_qty(self):
        try:
            balance = 1.0

            for from_process_id in self.from_detail_ids:
                # check sự thay đổi số lượng nhiều lần
                if from_process_id.qty != from_process_id.origin_qty and from_process_id.qty != from_process_id.qty_change:
                    balance = from_process_id.qty / from_process_id.origin_qty
                if balance != 1:
                    break

            for from_process_id in self.from_detail_ids:
                from_process_id.qty = balance * from_process_id.origin_qty
                from_process_id.qty_change = from_process_id.qty

            for to_process_id in self.to_detail_ids:
                to_process_id.qty = balance * to_process_id.origin_qty
        except Exception as e:
            raise ValidationError(e)


class ProductProcessDetail(models.Model):
    _name = "product.process.detail"

    from_process_id = fields.Many2one('product.process.line', "The from Process")
    to_process_id = fields.Many2one('product.process.line', "The to Process")
    product_id = fields.Many2one('product.product', string="Product", domain=[('type', '=', 'product')])
    uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    uom_id = fields.Many2one('uom.uom', string="Uom")
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    origin_qty = fields.Float(string="Origin Quantity", digits='Product Unit of Measure')
    qty = fields.Float(string="Quantity", digits='Product Unit of Measure')
    percent = fields.Float("Standard Price Percent")
    error_percent = fields.Float("Balance Percent")
    tracking = fields.Char(string='Tracking', compute='_compute_tracking')
    qty_change = fields.Float(string="Quantity Change", digits='Product Unit of Measure')

    @api.depends('product_id')
    def _compute_tracking(self):
        for item in self:
            item.tracking = item.product_id.tracking

    @api.onchange('qty')
    def _onchange_qty(self):
        if self.to_process_id or not self.from_process_id.to_detail_ids:
            return
        balance = self.qty / self.origin_qty
        for to_process_id in self.from_process_id.to_detail_ids:
            to_process_id.qty = balance * to_process_id.origin_qty

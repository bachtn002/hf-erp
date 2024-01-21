# -*- coding: utf-8 -*-

from odoo import models, fields, api

journal_type_dict = {
    'out_invoice': 'outgoing',
    'out_refund': 'incoming',
    'in_invoice': 'incoming',
    'in_refund': 'outgoing',
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_picking_type_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers')], string='Type picking',
                                                 compute='_compute_picking_type_code')

    @api.depends('move_type')
    def _compute_picking_type_code(self):
        for item in self:
            item.invoice_picking_type_code = journal_type_dict.get(item.move_type)

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountMove, self)._prepare_invoice_line_from_po_line(line)
        if self.env.context.get('from_picking_done_qty'):
            data['quantity'] = self.env.context.get('from_picking_done_qty')
        return data

    stock_picking_ids = fields.Many2many('stock.picking', 'table_account_invoice_stock_picking_relation', 'invoice_id',
                                         'picking_id',
                                         string="Picking Ref.")

    @api.onchange('stock_picking_ids')
    def _onchange_stock_pickings(self):
        if self.stock_picking_ids:
            self.line_ids = False
            self.invoice_line_ids = False
            new_lines = self.env['account.move.line']
            for stock_picking_id in self.stock_picking_ids:
                for move_id in stock_picking_id.move_lines:
                    new_line = new_lines.new(move_id._prepare_account_move_line_from_move(self))
                    new_line.account_id = new_line._get_computed_account()
                    new_line._onchange_price_subtotal()
                    new_lines += new_line
            new_lines._onchange_mark_recompute_taxes()
            origins = set(self.stock_picking_ids.mapped('name'))
            self.invoice_origin = ','.join(list(origins))

            refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
            refs = [ref for ref in refs if ref]
            self.ref = ','.join(refs)

            # Compute _invoice_payment_ref.
            if len(refs) == 1:
                self._invoice_payment_ref = refs[0]
            self._onchange_currency()
        elif self._origin.stock_picking_ids:
            self.line_ids = False
            self.invoice_line_ids = False

    @api.constrains('ref', 'move_type', 'partner_id', 'journal_id', 'invoice_date')
    def _check_duplicate_supplier_reference(self):
        return

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_revenues_decline = fields.Boolean(string="Revenues Decline", default=False)
    x_picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', copy=False)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_account(self):
        self.ensure_one()
        self = self.with_company(self.move_id.journal_id.company_id)

        if not self.product_id:
            return

        fiscal_position = self.move_id.fiscal_position_id
        accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            if self.move_id.move_type == 'out_invoice':
                return accounts['income'] or self.account_id
            else:
                return accounts['customer_return_account'] if accounts['customer_return_account'] else accounts['income']
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            if self.move_id.move_type == 'in_invoice':
                return accounts['expense'] or self.account_id
            else:
                return accounts['return_vendor_account'] if accounts['return_vendor_account'] else accounts['expense']

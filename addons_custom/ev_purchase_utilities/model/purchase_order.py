# -*- coding: utf-8 -*-

from datetime import date
import base64
import xlrd

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_open_wizard_import_po_line_by_excel(self):
        self.ensure_one()
        return {
            'name': _(''),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.purchase.order.line',
            'no_destroy': True,
            'target': 'new',
            'view_id': self.env.ref('ev_purchase_utilities.wizard_import_purchase_order_line_view_form') and self.env.ref('ev_purchase_utilities.wizard_import_purchase_order_line_view_form').id or False,
            'context': {'default_order_id': self.id},
        }

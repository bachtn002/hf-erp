# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _add_supplier_to_product(self):
        return

    def unlink(self):
        raise UserError(_('You can not delete'))

    def button_cancel(self):
        try:
            super(PurchaseOrder, self).button_cancel()
            if self.x_picking_confirm:
                raise UserError(_('Warehouse confirm you can not cancel'))
        except Exception as e:
            raise ValidationError(e)

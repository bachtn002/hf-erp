# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError, UserError


class StockTransfer(models.Model):
    _inherit = 'stock.transfer'

    def unlink(self):
        try:
            if not self.env.user.has_group('ev_stock_transfer_delete.group_delete_stock_transfer'):
                raise UserError(_('You do not have the right delete this stock transfer'))
            return super(StockTransfer, self).unlink()
        except Exception as e:
            raise ValidationError(e)

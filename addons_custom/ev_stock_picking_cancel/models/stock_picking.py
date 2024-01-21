# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError


class StockPickingCancel(models.Model):
    _inherit = 'stock.picking'

    def action_cancel_picking(self):
        self.mapped('move_lines')._action_cancel()
        self.write({'is_locked': True})
        return True

    def action_force_cancel_picking(self):
        self.mapped('move_lines').action_force_cancel()
        self.write({'is_locked': True})
        return True

    def action_set_to_draft(self):
        self.write({'state': 'draft'})
        self.mapped('move_lines')._action_set_to_draft()

    def unlink(self):
        raise UserError(_('You can not delete'))


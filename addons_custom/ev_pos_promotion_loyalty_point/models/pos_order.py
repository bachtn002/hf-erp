# -*- coding: utf-8 -*-

from odoo import _, models, api, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_note_member_app = fields.Char('Note member app')

    @api.model
    def _order_fields(self, ui_order):
        result = super(PosOrder, self)._order_fields(ui_order)
        result['x_note_member_app'] = ui_order.get('x_note_member_app', '')
        return result

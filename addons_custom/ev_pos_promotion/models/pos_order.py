# -*- coding: utf-8 -*-

from odoo import _, models, api, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _get_fields_for_order_line(self):
        res = super(PosOrder, self)._get_fields_for_order_line()
        res += ['promotion_id', 'promotion_applied_quantity']
        return res

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        return res

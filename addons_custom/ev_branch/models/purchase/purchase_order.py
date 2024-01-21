# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _default_branch_id(self):
        branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id, required=True)

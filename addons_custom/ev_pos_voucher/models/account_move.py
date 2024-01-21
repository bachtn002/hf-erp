# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPayment(models.Model):
    _inherit = 'account.move'

    x_is_move_voucher = fields.Boolean(default=False)

    def print_move_voucher(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_pos_voucher.move_voucher_xlsx/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }


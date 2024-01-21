# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    def _export_for_ui(self, payment):
        res = super(PosPayment, self)._export_for_ui(payment)
        if payment.x_lot_id:
            res.update({
                'lot_name': payment.x_lot_id.name,
            })
        return res


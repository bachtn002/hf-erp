# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    x_pos_shop_id = fields.Many2one('pos.shop', string='Pos shop', related='session_id.x_pos_shop_id', store=True,
                                    readonly=True)

    # Bỏ field
    security_user_no_shop = fields.Boolean(default=False)

    x_view_all_shop = fields.Boolean(default=True, string='View All Shop')

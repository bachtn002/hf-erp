# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    x_pos_shop_id = fields.Many2one('pos.shop', string='Pos shop', related='config_id.x_pos_shop_id', store=True,
                                    readonly=True)

    # Bỏ field
    security_user_no_shop = fields.Boolean(default=False)

    x_view_all_shop = fields.Boolean(default=True, string='View All Shop')



# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_pos_shop_id = fields.Many2one('pos.shop', string='Pos shop')

    x_price_correction = fields.Boolean(string="Price Correction", default=False)

    # Bỏ field
    security_user_no_shop = fields.Boolean(default=False)

    x_enable_lunisolar = fields.Boolean(string="Enable +/-", default=False)

    x_user_id = fields.Many2many('res.users', 'ev_pos_config_users', 'x_user_id' , 'pos_config_id',string='User')

    x_view_all_shop = fields.Boolean(default=True, string='View All Shop')

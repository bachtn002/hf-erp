# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosUser(models.Model):
    _inherit = 'res.users'

    x_pos_shop_ids = fields.Many2many('pos.shop', 'ev_pos_shops_users', 'user_id', 'pos_shop_id', string='Pos shop')

    # Bỏ field security_user_no_shop
    security_pos_shop = fields.Boolean(default=False, compute='_compute_security_pos_shop')

    x_pos_config_ids = fields.Many2many('pos.config', 'ev_pos_config_users', 'pos_config_id', 'x_user_id', string='Pos config')

    x_view_all_shop = fields.Boolean(default=False, string='View All Shop')

    # Bỏ field security_pos_shop
    @api.depends('x_pos_shop_ids')
    def _compute_security_pos_shop(self):
        for record in self:
            if record.x_pos_shop_ids:
                record.security_pos_shop = True
            else:
                record.security_pos_shop = False

    @api.onchange('x_pos_shop_ids')
    def _fill_pos_config(self):
        if self.x_pos_shop_ids:
            self.x_pos_config_ids = [(5,)]
            for conf in self.x_pos_shop_ids:
                for pos_id in conf.pos_config_ids.ids:
                    self.x_pos_config_ids = [(4, pos_id)]
        else:
            self.x_pos_config_ids = [(5,)]

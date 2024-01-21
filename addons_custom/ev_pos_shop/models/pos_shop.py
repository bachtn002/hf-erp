# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosShop(models.Model):
    _name = 'pos.shop'
    _description = 'Pos Shop'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    address = fields.Char(string='Address')
    phone = fields.Char(string='Phone')

    manage_shop_id = fields.Many2one('res.users', string='Manager shop')

    pos_config_ids = fields.One2many('pos.config', 'x_pos_shop_id', string='Pos config')

    user_ids = fields.Many2many('res.users', 'ev_pos_shops_users', 'pos_shop_id', 'user_id', string='User')

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    x_pos_shop_region_id = fields.Many2one('stock.region', 'Region', related='warehouse_id.x_stock_region_id')

    active = fields.Boolean(string='active', default=True)

    # Bỏ field
    security_user_no_shop = fields.Boolean(default=False)

    x_view_all_shop = fields.Boolean(default=True, string='View All Shop')


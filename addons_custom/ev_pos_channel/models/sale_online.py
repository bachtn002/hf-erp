# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOnline(models.Model):
    _inherit = 'sale.online'

    def _default_online_channel(self):
        return self.env['pos.channel'].search([('is_online_channel', '=', True)], limit=1).id

    pos_channel_id = fields.Many2one('pos.channel', string='Pos Channel', default=_default_online_channel)

    @api.model
    def sync_orders_online(self, config_id, fields):
        res = super(SaleOnline, self).sync_orders_online(config_id, fields)
        for item in res:
            sale_online = self.env['sale.online'].search([('name', '=', item['name']), ('pos_channel_id', '!=', False)])
            item.update({
                'pos_channel_id': sale_online.pos_channel_id.id
            })
        return res

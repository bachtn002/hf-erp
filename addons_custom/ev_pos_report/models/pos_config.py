# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        user_id = self.env['res.users'].search([('id', '=', self._uid)])
        shop_ids = []
        if user_id.branch_ids:
            for branch_id in user_id.branch_ids:
                pos_config_ids = self.env['pos.config'].search([('branch_id','=',branch_id.id),('active','=',True)])
                shop_ids += pos_config_ids.ids
        if user_id.branch_id:
            pos_config_ids = self.env['pos.config'].search([('branch_id','=',user_id.branch_id.id),('active','=',True)])
            shop_ids += pos_config_ids.ids
        if len(shop_ids) > 0:
            args += [('id', 'in', shop_ids)]
        return super(PosConfig, self).name_search(name, args=args, operator=operator, limit=limit)
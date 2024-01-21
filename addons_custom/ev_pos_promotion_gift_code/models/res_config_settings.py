# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_display_code = fields.Boolean(string='Is Display Code', default=False)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(is_display_code=self.env['ir.config_parameter'].sudo().get_param(
            'ev_pos_promotion_gift_code.is_display_code'))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        is_display_code = self.is_display_code and self.is_display_code or False
        param.set_param('ev_pos_promotion_gift_code.is_display_code', is_display_code)
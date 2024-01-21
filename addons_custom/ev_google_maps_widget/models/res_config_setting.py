from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_maps_api_key = fields.Char('Google maps api key')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            google_maps_api_key=self.env['ir.config_parameter'].sudo().get_param(
                'ev_google_maps_widget.google_maps_api_key'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()

        google_maps_api_key = self.google_maps_api_key and self.google_maps_api_key or False
        param.set_param('ev_google_maps_widget.google_maps_api_key', google_maps_api_key)

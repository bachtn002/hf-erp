# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

from ..helpers import GoogleMaps


class PosShop(models.Model):
    _inherit = 'pos.shop'

    lat = fields.Char('Lat')
    long = fields.Char('Long')
    x_pos_lat = fields.Char('Pos Lat')
    x_pos_long = fields.Char('Pos Long')
    country_state_id = fields.Many2one('res.country.state', string="Country")

    @api.onchange('x_pos_lat', 'x_pos_long')
    def _update_lat_long(self):
        self.lat = self.x_pos_lat
        self.long = self.x_pos_long

    def get_condition_searchbox(self):
        # allow search box (maps) can be display or not
        return True

    def set_lat_long(self, lat, long, address):
        try:
            self.lat = lat
            self.long = long
            # self.address = address
        except Exception as e:
            raise ValidationError(e)

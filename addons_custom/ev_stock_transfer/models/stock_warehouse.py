# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class StockLocation(models.Model):
    _inherit = "stock.location"

    x_transit_location = fields.Boolean('Transit location')

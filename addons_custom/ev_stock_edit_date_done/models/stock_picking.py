# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPickingEdit(models.Model):
    _inherit = 'stock.picking'

    date_done = fields.Datetime('Date of Transfer', copy=False, readonly=True,
                                help="Date at which the transfer has been processed or cancelled.", track_visibility='onchange')
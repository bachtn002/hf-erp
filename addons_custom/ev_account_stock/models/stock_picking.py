# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, ValidationError
from datetime import datetime, timedelta ,time
from odoo.osv import osv


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_is_posted = fields.Boolean(string="Is Posted", default=False, copy=False)
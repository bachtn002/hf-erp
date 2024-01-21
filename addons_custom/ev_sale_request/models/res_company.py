# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_time_request = fields.Float('Time Request')

    x_time_request_weekend = fields.Float('Time Request Weekend')

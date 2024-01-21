# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_employee_code_sync = fields.Char(string='Employee Code')

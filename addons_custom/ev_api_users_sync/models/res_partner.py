# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_position_sync = fields.Char(string='Position')
    x_department_sync = fields.Char(string='Department')
    x_start_working_date_sync = fields.Date(string='Date start work')
    x_end_working_date_sync = fields.Date(string='End date of work')
    x_employee_code = fields.Char(string='Employee Code')

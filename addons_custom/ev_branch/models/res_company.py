from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    x_code = fields.Char('Code')
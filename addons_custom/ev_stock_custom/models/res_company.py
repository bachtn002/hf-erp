from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    x_not_export_negative = fields.Boolean('Not export negative', default=True)

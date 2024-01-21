from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    x_voucher_code_rule_length = fields.Integer('Voucher code rule length', default=14)

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"
    
    x_complaint_hotline = fields.Char("Complaint Hotline")
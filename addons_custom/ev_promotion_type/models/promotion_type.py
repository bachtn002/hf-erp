from odoo import models, fields, api

class PromotionType(models.Model):
    _name = 'promotion.type'
    _description = 'Danh muc loai CTKM'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
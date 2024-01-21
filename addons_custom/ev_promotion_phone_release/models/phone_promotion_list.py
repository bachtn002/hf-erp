from odoo import api, fields, models


class PhonePromotionList(models.Model):
    _name = 'phone.promotion.list'
    _rec_name = 'promotion_code'
    _description = 'Phone Promotion List'

    promotion_code = fields.Char("Promotion code")
    phone = fields.Char("Phone")
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('available', 'Available'),
        ('used', 'Used'),
        ('cancel', 'Cancel')
    ], default='new', string='Status', )

    promotion_voucher_id = fields.Many2one('promotion.voucher', "Promotion voucher")

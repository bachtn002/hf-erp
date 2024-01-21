from datetime import date

from odoo import models, fields


class PromotionVoucherStatus(models.Model):
    _name = 'promotion.voucher.status'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Promotion Voucher Status'

    promotion_voucher_status_id = fields.Many2one(comodel_name='promotion.voucher', string='Promotion Voucher Reference',
                                           ondelete='cascade')
    promotion_code = fields.Char('Promotion Code')
    # promotion_code = fields.Many2one('promotion.voucher.line','Promotion Code')
    pos_order = fields.Many2one('pos.order', string='Pos Order')
    date = fields.Char('Date')
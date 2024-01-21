from odoo import api, fields, models


class PromotionVoucherConfirm(models.TransientModel):
    _name = 'promotion.voucher.confirm'
    _description = 'Promotion Voucher Confirm'

    message = fields.Char("Message")
    promotion_voucher_id = fields.Many2one('promotion.voucher', "Promotion voucher")


    def btn_yes(self):
        self.promotion_voucher_id.action_active()
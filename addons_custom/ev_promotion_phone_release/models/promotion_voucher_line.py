from odoo import api, fields, models


class PromotionVoucherLine(models.Model):
    _inherit = 'promotion.voucher.line'

    def check_promotion(self, name, customerID):
        data = {}
        lot_id = self.search([('name', '=', name)], limit=1)
        # Check Promotion code phát hành theo số điện thoại được apply
        if lot_id.promotion_voucher_id.x_release_phone_types == 'phone':
            partner_id = self.env['res.partner'].browse(customerID)
            couple_phone_code = self.env['phone.promotion.list'].search(
                [('phone', '=', partner_id.phone), ('promotion_code', '=', name), ('promotion_voucher_id.state', '=', 'active'), ('state', '=', 'available')])
            if couple_phone_code:
                data = {
                    'type': 'valid',
                    'promotion_id': lot_id.promotion_voucher_id.promotion_id.type,
                    'lot_id': lot_id.id,
                    'get_promotion_id': lot_id.promotion_voucher_id.promotion_id.id,
                    'code_promotion': lot_id.name
                }
        else:
            data = {
                'type': 'valid',
                'promotion_id': lot_id.promotion_voucher_id.promotion_id.type,
                'lot_id': lot_id.id,
                'get_promotion_id': lot_id.promotion_voucher_id.promotion_id.id,
                'code_promotion': lot_id.name
            }
        return data

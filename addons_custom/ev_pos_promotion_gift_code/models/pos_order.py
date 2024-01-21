# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_promotion_gift_code_history_ids = fields.One2many('pos.promotion.gift.code.history', 'pos_order_id',
                                                        string='Pos Promotion Gift Code History')

    @api.model
    def create_from_ui(self, orders, draft=False):
        try:
            res = super(PosOrder, self).create_from_ui(orders, draft)
            for order in orders:
                partner_id = self.env['res.partner'].browse(order['data']['partner_id'])
                if len(order['data']['list_code_gave_away']) > 0:
                    for item in order['data']['list_code_gave_away'][0]:
                        self.env['pos.promotion.gift.code.history'].create({
                            'promotion_id': item['promotion_id'],
                            'pos_promotion_id': item['pos_promotion_id'],
                            'phone': partner_id.phone,
                            'gift_code': item['code_for_save'],
                            'pos_order_id': res[0]['id'],
                            'partner_id': partner_id.id,
                        })
                        self.env['phone.promotion.list'].create({
                            'promotion_code': item['code_for_save'],
                            'phone': partner_id.phone,
                            'state': 'available',
                            'promotion_voucher_id': item['promotion_voucher_id'],
                        })
            return res
        except Exception as e:
            raise ValidationError(e)

    def refund(self):
        try:
            res = super(PosOrder, self).refund()
            gift_code_history = self.env['pos.promotion.gift.code.history'].search(
                [('partner_id', '=', self.partner_id.id), ('pos_order_id', '=', self.id)])
            for item in gift_code_history:
                phone_promotion_list = self.env['phone.promotion.list'].search(
                    [('promotion_code', '=', item.gift_code), ('phone', '=', item.phone), ('state', '!=', 'used')])
                if phone_promotion_list:
                    phone_promotion_list.sudo().unlink()
            return res
        except Exception as e:
            raise ValidationError(e)

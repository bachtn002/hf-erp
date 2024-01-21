# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        try:
            res = super(PosOrder, self).create_from_ui(orders, draft)
            phone_apply = False
            _code_promotion = []
            # số lần sử dụng mã promotion code
            for item in orders[0]['data']['lines']:
                code_promotion = False
                if item[2]['promotion_code']:
                    code_promotion =  item[2]['promotion_code']
                if code_promotion and code_promotion not in _code_promotion:
                    _code_promotion.append(code_promotion)
                    _logger.error('========code_promotion === %s' % code_promotion)
                    pos_reference = orders[0]['id']
                    customer_id = orders[0]['data']['partner_id']
                    promotion_voucher_line = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])
                    promotion_voucher = promotion_voucher_line.promotion_voucher_id
                    date_used = str(datetime.today().date().strftime("%d/%m/%Y"))

                    if customer_id and promotion_voucher.x_release_phone_types == 'phone':
                        partner_id = self.env['res.partner'].browse(customer_id)
                        phone_apply = partner_id.phone
                        phone_line = self.env['phone.promotion.list'].search(
                            [('promotion_code', '=', code_promotion), ('phone', '=', partner_id.phone)], limit=1)
                        if phone_line:
                            phone_line.state = 'used'

                    if phone_apply:
                        self._cr.execute(
                            f"""INSERT INTO promotion_voucher_count(promotion_voucher_count_id,promotion_code,pos_order_uid,date,phone_number_applied) 
                                VALUES ('{promotion_voucher.id}','{code_promotion}','{pos_reference}','{date_used}','{phone_apply}')""")
                    else:
                        self._cr.execute(
                            f"""INSERT INTO promotion_voucher_count(promotion_voucher_count_id,promotion_code,pos_order_uid,date) 
                                        VALUES ('{promotion_voucher.id}','{code_promotion}','{pos_reference}','{date_used}')""")
                    promotion_voucher_count_records = self.env['promotion.voucher.count'].search(
                        [('promotion_voucher_count_id', '=', promotion_voucher.id)])
                    count_code = 0  # số mã code trong bảng tạm
                    for rc in promotion_voucher_count_records:
                        if code_promotion == rc.promotion_code:
                            count_code += 1
                    lines = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])

                    count_code_use = promotion_voucher.promotion_use_code - count_code

                    if lines.promotion_use_code == 1:
                        lines.write({
                            'state_promotion_code': 'used',
                            'promotion_use_code': 0
                        })
                    else:
                        lines.promotion_use_code = count_code_use
            return res
        except Exception as e:
            raise ValidationError(e)

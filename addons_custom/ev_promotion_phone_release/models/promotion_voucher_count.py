from odoo import api, fields, models, _
from datetime import date, datetime


class PromotionVoucherCount(models.Model):
    _inherit = 'promotion.voucher.count'

    phone_number_applied = fields.Char("Phone number applied")

    def check_promotion_code(self, pos_reference, code_promotion, customerID):
        # số bản ghi promotion code đã sử dụng trong bảng promotion.voucher.count
        record_promotion_code = self.env['promotion.voucher.count'].search([('promotion_code', '=', code_promotion)])
        length_code_table = len(record_promotion_code)
        promotion_voucher_line = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)])
        # promotion_use_code = promotion_voucher_line.promotion_use_code
        promotion_use_code = promotion_voucher_line.promotion_voucher_id.promotion_use_code
        data = {}
        promotion_voucher_lines = self.search([])
        if promotion_voucher_line.id != False:
            record_same_pr_code = self.env['promotion.voucher.count'].search(
                [('pos_order_uid', '=', pos_reference),
                 ('promotion_voucher_count_id', '=', promotion_voucher_line.promotion_voucher_id.id)])
        else:
            record_same_pr_code = []
        lot_id = self.env['promotion.voucher.line'].search([('name', '=', code_promotion)], limit=1)
        if not lot_id:
            data['type'] = 'existed'
            data['message'] = _('Code "%s" not exist in database. Please check!') % code_promotion
            return data
        if lot_id.state_promotion_code != 'available':
            data['type'] = 'not_activated'
            data[
                'message'] = _('Code "%s" not use promotion. Please check!') % code_promotion
            return data
        # Nếu số bản ghi trong lịch sử sử dụng = số lần sử dụng của mã tương ứng => Mã đã sử dụng hết số lần
        if length_code_table == promotion_use_code:
            data['type'] = 'not_exp'
            data[
                'message'] = _('Code "%s" not use promotion. Please check!') % code_promotion
            return data
        if len(record_same_pr_code) > 0:
            data['type'] = 'not_exp'
            data['message'] = _('Order used promotion code. Please check!')
            return data
        if lot_id.expired_date and lot_id.expired_date < date.today():
            data['type'] = 'not_exp'
            data['message'] = _('Code "%s" expired date.') % lot_id.name
            return data
        # Mã code phát hành theo số điện thoại bắt buộc nhập khách hàng
        if lot_id.promotion_voucher_id.x_release_phone_types == 'phone':
            if not customerID:
                data['type'] = 'customer_not_enter'
                data['message'] = _('Promotion code is apply for specific Phone number, Please enter the Customer')
                return data
            partner_id = self.env['res.partner'].browse(customerID)
            couple_phone_code = self.env['phone.promotion.list'].search(
                [('phone', '=', partner_id.phone), ('promotion_code', '=', code_promotion),
                 ('promotion_voucher_id.state', '=', 'active')])
            if not couple_phone_code:
                data['type'] = 'customer_not_valid'
                data['message'] = _('Customer is not corresponding with promotion code')
                return data
            elif couple_phone_code.state != 'available':
                data['message'] = _('Code "%s" not use promotion. Please check!') % code_promotion
                return data
        data = {
            'type': 'valid',
            'promotion_id': lot_id.promotion_voucher_id.promotion_id.type,
            'lot_id': lot_id.id,
            'get_promotion_id': lot_id.promotion_voucher_id.promotion_id.id,
            'code_promotion': lot_id.name
        }
        return data

    def update_promotion_used(self, pos_reference, code_promotion, customer_id):
        phone_apply = False
        # số lần sử dụng mã promotion code
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
            lines.state_promotion_code = 'used'
            lines.promotion_use_code = 0
        else:
            lines.promotion_use_code = count_code_use

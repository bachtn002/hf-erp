# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class StockProductLot(models.Model):
    _inherit = 'stock.production.lot'

    # tính toán số tiền của PMH
    def _compute_infor_voucher(self):
        # print('state', self.x_state)
        if not self.product_id.x_is_voucher:
            raise except_orm('Thông báo',
                             ('Mã "%s" không phải là mã của phiếu mua hàng. Vui lòng kiểm tra lại!' % self.name))
        if self.x_state != 'available':
            raise except_orm('Thông báo',
                             ('Mã "%s" hiện không ở trạng thái đang sử dụng. Vui lòng kiểm tra lại!' % self.name))
        elif self.expiration_date and self.expiration_date.date() < date.today():
            raise except_orm('Thông báo', ('Mã "%s" đã hết hạn.' % self.name))
        return True

    def _compute_amount_voucher(self, amount):
        self._compute_infor_voucher()
        if self.product_id.x_card_discount > 0:
            amount_discount = round(amount * self.product_id.x_card_discount / 100, 0)
            if self.product_id.x_card_value == 0:
                return amount_discount
            if amount_discount < self.product_id.x_card_value:
                return amount_discount
            else:
                return self.product_id.x_card_value
        if amount > self.product_id.x_card_value:
            return self.product_id.x_card_value
        return amount

    # lấy các sản phẩm và số lượng thanh toán
    def _get_product_payment(self):
        if len(self.product_id.x_product_card_ids) == 0 and len(self.product_id.x_product_category_card_ids) == 0:
            return True
        list = []
        for line in self.product_id.x_product_card_ids:
            list.append((line.product_allow_id.id, line.maximum_quantity))
        for line in self.product_id.x_product_category_card_ids:
            product_ids = self.env['product.product'].search([('categ_id', '=', line.product_category_allow_id.id)])
            for product_id in product_ids:
                list.append((product_id.id, line.maximum_quantity))
        return list  # list các tuple

    # kiem tra phương thuc su dung
    def _check_customer_use_type(self, partner_id):
        if self.x_release_id.use_type == 'fixed':
            if self.x_customer_id.id != partner_id.id:
                raise except_orm('Thông báo', (
                        'PMH có mã "%s" được sử dụng đích danh cho khách hàng khác. Vui lòng kiểm tra lại!' % self.name))
        return True

    def _check_type_voucher(self):
        if 0 < self.product_id.x_card_discount < 100:
            return 'CP'
        return 'VC'

    def check_code_from_ui(self, code, customer_id):
        data = {}
        if not code:
            data['type'] = 'existed'
            data['message'] = 'Lỗi dữ liệu. Vui lòng kiểm tra lại!'
            return data
        # code = code.strip().upper()
        code = code.strip()
        lot_id = self.search([('name', '=', code)], limit=1)
        if not lot_id:
            data['type'] = 'existed'
            data['message'] = 'Mã "%s" không tồn tại trên hệ thống. Vui lòng kiểm tra lại!' % code
            return data
        if not lot_id.product_id.x_is_voucher:
            data['type'] = 'not_voucher'
            data['message'] = 'Mã "%s" không phải là mã của phiếu mua hàng. Vui lòng kiểm tra lại!' % code
            return data
        else:
            if not lot_id.product_id.sale_ok:
                data['type'] = 'not_sale_ok'
                data['message'] = 'Mã "%s" không được phép bán. Vui lòng kiểm tra lại!' % code
                return data
        if lot_id.x_state != 'activated':
            data['type'] = 'not_activated'
            data['message'] = 'Mã "%s" hiện không ở trạng thái có thể bán. Vui lòng kiểm tra lại!' % code
            return data
        if lot_id.expiration_date and lot_id.expiration_date.date() < date.today():
            data['type'] = 'not_exp'
            data['message'] = 'Mã "%s" đã hết hạn.' % code
            return data
        if lot_id.x_release_id.use_type == 'fixed' and not customer_id:
            data['type'] = 'not_customer_id'
            data['message'] = 'Mã "%s" là loại phiếu mua hàng sử dụng đích danh. Vui lòng lựa chọn KH.' % code
            return data
        data = {
            'type': 'valid',
            'product_id': lot_id.product_id.id,
            'lot_id': lot_id.id,
        }
        return data

    def _check_code_payment_from_ui(self, lot_name, customer_id=False, amount_due=1, config_id=False, promotion=False):
        data = {}
        if amount_due <= 0:
            data['type'] = 'amount_due'
            data['message'] = 'Đã thanh toán đủ. Vui lòng kiểm tra lại!'
            return data
        # code = lot_name.strip().upper()
        code = lot_name.strip()
        lot_id = self.search([('name', '=', code)], limit=1)
        if not lot_id:
            data['type'] = 'existed'
            data['message'] = 'Mã "%s" không tồn tại trên hệ thống. Vui lòng kiểm tra lại!' % code
            return data
        if not lot_id.product_id.x_is_voucher:
            data['type'] = 'not_voucher'
            data['message'] = 'Mã "%s" không phải là mã của phiếu mua hàng. Vui lòng kiểm tra lại!' % code
            return data
        if lot_id.x_state != 'available':
            data['type'] = 'not_available'
            data['message'] = 'Mã "%s" hiện không ở trạng thái có thể sử dụng. Vui lòng kiểm tra lại!' % code
            return data
        if lot_id.expiration_date and lot_id.expiration_date.date() < date.today():
            data['type'] = 'not_exp'
            data['message'] = 'Mã "%s" đã hết hạn.' % code
            return data
        if lot_id.x_release_id.use_type == 'fixed':
            if not customer_id:
                data['type'] = 'not_customer_id'
                data['message'] = 'Mã "%s" là loại phiếu mua hàng sử dụng đích danh. Vui lòng lựa chọn KH.' % code
                return data
            elif lot_id.x_customer_id and customer_id and lot_id.x_customer_id.id != customer_id:
                data['type'] = 'not_equal_customer'
                data[
                    'message'] = 'Mã "%s" là loại phiếu mua hàng sử dụng đích danh. Vui lòng kiểm tra thông tin KH.' % code
                return data
        return data

    def check_code_payment_from_ui(self, lot_name, products, customer_id, payments, amount_total, amount_due, config_id,
                                   promotion):
        data = self._check_code_payment_from_ui(lot_name, customer_id, amount_due, config_id, promotion)
        if 'message' in data:
            return data
        # code = lot_name.strip().upper()
        code = lot_name.strip()
        lot_id = self.search([('name', '=', code)], limit=1)
        if lot_id.x_state != 'available':
            data['type'] = 'not_activated'
            data['message'] = 'Mã "%s" hiện không ở trạng thái có thể sử dụng. Vui lòng kiểm tra lại!' % code
            return data

        return self._compute_amount_payment(lot_id, products, payments, amount_total, amount_due)

    def _compute_amount_payment(self, lot_id, products, payments, amount_total, amount_due):
        lot_vc_ids = []
        lot_cp_ids = []
        amount_paid_from_voucher = 0
        if lot_id.product_id.x_card_discount > 0 and lot_id.product_id.x_card_discount < 100:
            lot_cp_ids.append(lot_id)
        else:
            lot_vc_ids.append(lot_id)
        for payment in payments:
            # comment fix lỗi không dùng được nhiều voucher
            # amount_paid_from_voucher += payment['amount']
            # code = payment['lot_name'].strip().upper()

            code = payment['lot_name'].strip()
            pay_lot_id = self.search([('name', '=', code)], limit=1)
            if pay_lot_id.id == lot_id.id:
                data = {
                    'type': 'duplicate',
                    'message': 'Mã "%s" bạn đã nhập trước đó. Vui lòng kiểm tra thông tin thanh toán.' % code,
                }
                return data
            # comment fix lỗi không dùng được nhiều voucher
            # if pay_lot_id.product_id.x_card_discount > 0 and pay_lot_id.product_id.x_card_discount < 100:
            #     lot_cp_ids.append(pay_lot_id)
            # else:
            #     lot_vc_ids.append(pay_lot_id)
        amount_paid_method_other = amount_total - amount_paid_from_voucher - amount_due
        amount_to_pay = amount_check = amount_paid_from_voucher + amount_due
        # for lot_vc_id in lot_vc_ids:
        #     list_product = lot_vc_id._get_product_payment()
        #     if list_product in (True, []):
        #         amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_pay)
        #     else:
        #         amount_p = 0
        #         for item in products:
        #             for product in list_product:
        #                 if item['product_id'] == product[0]:
        #                     if product[1] == 0:
        #                         amount_p += item['price']
        #                     else:
        #                         if item['quantity'] > product[1]:
        #                             amount_p += item['price'] / item['quantity'] * product[1]
        #                         else:
        #                             amount_p += item['price']
        #         if amount_p == 0:
        #             return {
        #                 'type': 'valid',
        #                 'amount': 0,
        #             }
        #         amount_to_list_product = min(amount_to_pay, amount_p)
        #         amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_list_product)

        # áp dụng với trường hợp giảm giá
        for lot_vc_id in lot_vc_ids:
            list_product = lot_vc_id._get_product_payment()
            if list_product in (True, []):
                amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_pay)
            # nếu không chọn điều kiện và và điều kiện hoặc thì áp dụng voucher với tất cả các SP trong giỏ hàng
            elif lot_id.product_id.x_and_condition == False and lot_id.product_id.x_or_condition == False:
                amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_pay)
            else:
                amount_p = 0
                check_or_conditon = 0
                check_and_condition = 0
                # với điều kiện và áp dụng voucher
                if lot_id.product_id.x_and_condition:
                    for item in products:
                        for product in list_product:
                            if item['product_id'] == product[0]:
                                check_and_condition += 1
                    if check_and_condition == len(list_product):
                        amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_pay)
                    else:
                        data = {
                            'type': 'duplicate',
                            'message': 'Mã voucher không hợp lệ. SP điều kiện chưa đủ trong đơn hàng với điều kiện và',
                        }
                        return data
                    # với điều kiện hoặc voucher
                if lot_id.product_id.x_or_condition:
                    for item in products:
                        for product in list_product:
                            if item['product_id'] == product[0]:
                                check_or_conditon += 1
                    if check_or_conditon > 0:
                        amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_pay)
                    else:
                        data = {
                            'type': 'duplicate',
                            'message': 'Mã voucher không hợp lệ. SP điều kiện không có trong đơn hàng ',
                        }
                        return data
                # for item in products:
                #     for product in list_product:
                #         if item['product_id'] == product[0]:
                #             if product[1] == 0:
                #                 amount_p += item['price']
                #             else:
                #                 if item['quantity'] > product[1]:
                #                     amount_p += item['price'] / item['quantity'] * product[1]
                #                 else:
                #                     amount_p += item['price']
                # if amount_p == 0:
                #     data = {
                #         'type': 'duplicate',
                #         'message': 'Mã voucher không hợp lệ. SP điều kiện không có trong đơn hàng',
                #     }
                #     return data
                # amount_to_list_product = min(amount_to_pay, amount_p)
                # amount_to_pay -= lot_vc_id._compute_amount_voucher(amount_to_list_product)
        for lot_cp_id in lot_cp_ids:
            list_product = lot_cp_id._get_product_payment()
            if list_product in (True, []):
                amount_to_pay -= lot_cp_id._compute_amount_voucher(amount_to_pay)
            else:
                amount_p = 0
                for item in products:
                    for product in list_product:
                        if item['product_id'] == product[0]:
                            if product[1] == 0:
                                amount_p += item['price']
                            else:
                                if item['quantity'] > product[1]:
                                    amount_p += item['price'] / item['quantity'] * product[1]
                                else:
                                    amount_p += item['price']
                if amount_p == 0:
                    # return {
                    #     'type': 'valid',
                    #     'amount': 0,
                    # }
                    data = {
                        'type': 'duplicate',
                        'message': 'Mã voucher không hợp lệ. SP điều kiện không có trong đơn hàng',
                    }
                    return data
                amount_to_list_product = min(amount_to_pay, amount_p)
                amount_to_pay -= lot_cp_id._compute_amount_voucher(amount_to_list_product)
        amount = amount_check - amount_to_pay - amount_paid_from_voucher
        if amount < 0:
            data = {
                'type': 'amountneg',
                'message': 'Vui lòng kiểm tra thông tin thanh toán (Phiếu mua hàng phải thanh toán sau cùng).',
            }
            return data
        return {
            'type': 'valid',
            'amount': amount,
        }

    def check_code_from_ui_validate(self, list_voucher_to_sale, list_voucher_to_payment, customer_id, config_id):
        for voucher_to_sale in list_voucher_to_sale:
            data = self.check_code_from_ui(voucher_to_sale, customer_id)
            if 'message' in data:
                return data
        for voucher_to_payment in list_voucher_to_payment:
            data = self._check_code_payment_from_ui(voucher_to_payment, customer_id, config_id=config_id)
            if 'message' in data:
                return data
        return {}

    # cập nhật trạng thái voucher khi sử dụng
    def update_voucher_status_after_used(self, voucher_code):
        lot_id = self.search([('name', '=', voucher_code)], limit=1)
        lot_id.x_state = 'used'

    def update_voucher_status_after_delete(self, voucher_code):
        lot_id = self.search([('name', '=', voucher_code)], limit=1)
        lot_id.x_state = 'available'

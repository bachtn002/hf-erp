# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError
import hashlib
import requests
import json
from datetime import datetime, timedelta
import base64


class PaymentQRCodeTransaction(models.Model):
    _name = 'payment.qrcode.transaction'
    _description = 'Payment QRCode Transaction'
    _order = 'id desc'

    order_id = fields.Many2one('pos.order', string='Pos Order')
    # payment_id = fields.Many2one('pos.payment', string='Pos Payment')
    state = fields.Selection([
        ('paid', 'Paid'),
        ('checked', 'Checked')
    ], string='State', default='paid')

    pg_amount = fields.Char(string='PG Amount', help='Số tiền thanh toán')
    pg_currency = fields.Char(string='PG Currency', help='Đơn vị tiền tệ')
    pg_merchant_id = fields.Char(string='PG Merchant ID', help='Mã định danh merchant do MB cấp')
    pg_order_info = fields.Char(string='PG Order Info', help='Nội dung thanh toán')
    pg_order_reference = fields.Char(string='PG Order Reference', help='Mã tham chiếu giao dịch phía merchant',
                                     index=True)
    pg_payment_method = fields.Char(string='PG Payment Method', help='Mã phương thức thanh toaán')
    pg_card_number = fields.Char(string='PG Card Number', help='Số tài khoản ngân hàng/Số thẻ sử dụng thanh toán')
    pg_card_holder_name = fields.Char(string='PG Card Holder Name', help='Tên chủ thẻ')
    pg_payment_channel = fields.Char(string='PG Payment Channel', help='Kênh thực hiện giao dịch của khách hàng')
    pg_transaction_number = fields.Char(string='PG Transaction Number', help='Mã giao dịch phía MB')
    pg_issuer_txn_reference = fields.Char(string='PG Issuer TXN Reference', help='Mã giao dịch phía issuer')
    pg_issuer_code = fields.Char(string='PG Issuer Code', help='Mã tổ chức phát hành')
    error_code = fields.Char(string='Error Code', help='Mã code trả về cho merchant')
    pg_issuer_response_code = fields.Char(string='PG Issuer Response Code', help='Mã code issuer trả về')
    pg_paytime = fields.Char(string='PG Paytime', help='Thời gian giao dịch - <ddMMyyyyHHmiss>')
    session_id = fields.Char(string='Session ID',
                             help='Mã session thanh toán định danh cho giao dịch thanh toán vừa tạo')
    pos_session_id = fields.Many2one('pos.session', string='Pos Session')
    mac = fields.Char(string='MAC')
    mac_type = fields.Char(string='MAC Type')
    order_reference = fields.Char('Order Reference', index=True)
    pos_shop_id = fields.Many2one('pos.shop', string='Pos Shop')
    view_all_shop = fields.Boolean(default=True)

    def hash_mac_md5(self, input):

        hash_secret_key = self.env['ir.config_parameter'].sudo().get_param('mbpay_hash_secret_key')
        hash_md5 = hashlib.new('md5')
        hash_md5.update(hash_secret_key.encode())
        hash_md5.update(input.encode())
        return hash_md5.hexdigest().upper()

    def action_api__mbpay_create_order(self, params):
        try:
            # ipn_url
            ipn_url = self.env['ir.config_parameter'].sudo().get_param('mbpay_ipn_url')
            access_code = self.env['ir.config_parameter'].sudo().get_param('mbpay_access_code')
            params['ipn_url'] = ipn_url
            params['access_code'] = access_code

            filtered_data = {key: value for key, value in params.items() if
                             value is not None and value != "" and key not in ["mac_type", "mac"]}
            sorted_data = sorted(filtered_data.items(), key=lambda x: x[0])
            query_string = '&'.join(['{}={}'.format(key, value) for key, value in sorted_data])

            # Hash MAC MD5
            mac = self.hash_mac_md5(query_string)
            params['mac'] = mac

            # Call api create order
            url = self.env['ir.config_parameter'].sudo().get_param('mbpay_api_create_order')
            payload = params
            headers = {
                'Content-Type': 'application/json'
            }
            time_sent_request_create_order = (datetime.now() + timedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S.%f')
            response = requests.request('POST', url, headers=headers, data=json.dumps(payload))
            time_received_response_create_order = (datetime.now() + timedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S.%f')
            result = json.loads(response.text)

            # Save session_id for HMAC webhook
            self.env['payment.create.order.qrcode.res'].sudo().create({
                'response': str(result),
                'session_id': result['session_id'],
                'pg_order_reference': result['order_reference'],
                'time_sent_request_create_order': time_sent_request_create_order,
                'time_received_response_create_order': time_received_response_create_order,
            })

            result['expire_time'] = datetime.strptime(result['expire_time'], '%d-%m-%Y %H:%M:%S').strftime(
                '%m-%d-%Y %H:%M:%S')

            # Get base64 image qrcode
            payload = {}
            headers = {}
            url = result['qr_url']
            if url:
                response = requests.request("GET", url, headers=headers, data=payload)
                base64_img_qrcode = base64.b64encode(response.content).decode('utf-8')
                result['qr_base64'] = base64_img_qrcode
            return result
        except Exception as ex:
            return None

    def action_api__mbpay_paygate_detail(self, params, input_md5):
        try:
            # Hash MAC MD5
            mac = self.hash_mac_md5(input_md5)
            params['mac'] = mac

            # Call api paygate detail
            url = self.env['ir.config_parameter'].sudo().get_param('mbpay_api_paygate_detail')
            payload = params
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request('POST', url, headers=headers, data=json.dumps(payload))
            result = json.loads(response.text)
            
            # Insert payment.qrcode.transaction if payment success
            if result['error_code'] == '00':
                order_reference = result['order_reference'][4:-4]
                payment_qrcode_transaction = self.env['payment.qrcode.transaction'].sudo().search([('order_reference', '=', order_reference)])
                if not payment_qrcode_transaction:
                    pg_paytime = result['trans_time']
                    day = pg_paytime[:2]
                    month = pg_paytime[2:4]
                    year = pg_paytime[4:8]
                    hour = pg_paytime[8:10]
                    minute = pg_paytime[10:12]
                    second = pg_paytime[12:14]
                    self.env['payment.qrcode.transaction'].sudo().create({
                        'order_reference': order_reference,
                        'mac': result['mac'],
                        'mac_type': result['mac_type'],
                        'pg_amount': result['amount'],
                        'pg_currency': result['currency'],
                        'pg_merchant_id': result['merchant_id'],
                        'pg_order_info': result['order_info'],
                        'pg_order_reference': result['order_reference'],
                        'pg_payment_method': result['pg_payment_method'],
                        'pg_paytime': f"{year}-{month}-{day} {hour}:{minute}:{second}",
                        'pg_transaction_number': result['transaction_number'],
                        'pg_issuer_code': result['issuer'],
                        'error_code': result['error_code'],
                    })
            return result
        except Exception as ex:
            return None

    def action_api__mbpay_paygate_refund(self, params, input_md5):
        try:
            pass
        except Exception as ex:
            return ex

    def action_check_pg_order_reference(self, pg_order_reference):
        try:
            sql = """
                SELECT pg_order_reference,
                       error_code
                FROM payment_qrcode_transaction
                WHERE pg_order_reference = '%s'
                ORDER BY id LIMIT 1;
            """
            self._cr.execute(sql % pg_order_reference)
            res = self._cr.dictfetchall()
            if res and res[0]['error_code'] == '00':
                return True
            return False
        except Exception as ex:
            return ex

    def action_check_order_reference(self, order_reference, amount_payment_qrcode):
        sql = """
            SELECT pg_amount FROM payment_qrcode_transaction WHERE order_reference = '%s' ORDER BY id LIMIT 1;
        """
        self._cr.execute(sql % order_reference)
        res = self._cr.dictfetchall()
        if res:
            if float(res[0]['pg_amount']) == float(amount_payment_qrcode):
                return True
        return False

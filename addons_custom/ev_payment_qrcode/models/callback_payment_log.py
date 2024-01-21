# -*- coding: utf-8 -*-
import ast
from odoo import models, fields, api
from odoo.exceptions import UserError


class CallbackPaymentLog(models.Model):
    _name = 'callback.payment.log'
    _description = 'Callback Payment Log'
    _order = 'id desc'

    ip_request = fields.Char("Ip request")
    response = fields.Text('Response')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('error', 'Error'),
        ('done', 'Done')
    ], default='draft', string='State')
    type = fields.Selection([
        ('log_mb_payment_result', 'MB Payment Result'),
        ('log_checked_payment_result', 'Checked Payment Result')
    ], string='Type')

    def action_payment_qrcode_transaction(self):
        if self.state == 'draft':
            self.state = 'queue'
            self.sudo().with_delay(channel='root.action_qrcode_transaction', max_retries=3)._action_done()

    def _action_done(self):
        try:
            data = ast.literal_eval(self.response)
            payment_qrcode_transaction = self.env['payment.qrcode.transaction'].search(
                [('pg_order_reference', '=', data['pg_order_reference'])])
            if payment_qrcode_transaction:
                self.state = 'done'
                return
            pg_paytime = data['pg_paytime'][0:4] + '-' + data['pg_paytime'][4:6] + '-' + data['pg_paytime'][6:8] + ' ' + \
                         data['pg_paytime'][8:10] + ':' + data['pg_paytime'][10:12] + ':' + data['pg_paytime'][12:14]
            pos_shop_id = self.env['pos.shop'].sudo().search([('merchant_id', '=', data['pg_merchant_id'])], limit=1).id
            val = {
                # 'session_id': data['session_id'],
                'pg_amount': data['pg_amount'],
                'pg_currency': data['pg_currency'],
                'pg_merchant_id': data['pg_merchant_id'],
                'pg_order_info': data['pg_order_info'],
                'pg_order_reference': data['pg_order_reference'],
                'pg_payment_method': data['pg_payment_method'],
                'pg_card_number': data['pg_card_number'] if 'pg_card_number' in data else None,
                'pg_card_holder_name': data['pg_card_holder_name'] if 'pg_card_holder_name' in data else None,
                'pg_payment_channel': data['pg_payment_channel'],
                'pg_transaction_number': data['pg_transaction_number'],
                'pg_issuer_txn_reference': data['pg_issuer_txn_reference'],
                'pg_issuer_code': data['pg_issuer_code'],
                'error_code': data['error_code'],
                'pg_issuer_response_code': data['pg_issuer_response_code'],
                'pg_paytime': pg_paytime,
                'mac': data['mac'],
                'mac_type': data['mac_type'],
                'order_reference': data['pg_order_reference'][4:-4],
                'pos_shop_id': pos_shop_id,
            }
            payment_qrcode_transaction = self.env['payment.qrcode.transaction'].sudo().create(val)
            if payment_qrcode_transaction:
                self.state = 'done'
            else:
                self.state = 'error'
        except Exception as ex:
            raise UserError(ex)

    def action_map_data_payment_qrcode(self):
        if self.state == 'draft':
            self.state = 'queue'
            self.sudo().with_delay(channel='root.action_qrcode_transaction',
                                   max_retries=3)._action_map_data_payment_qrcode()

    def _action_map_data_payment_qrcode(self):
        try:
            res = ast.literal_eval(self.response)
            pos_session_id = res['pos_session_id']
            order_id = res['order_id']
            order_reference = res['order_reference']
            pos_shop_id = res['pos_shop_id']
            payment_qrcode_transaction = self.env['payment.qrcode.transaction'].sudo().search(
                [('order_reference', '=', order_reference)])
            if payment_qrcode_transaction:
                if len(payment_qrcode_transaction) > 1:
                    create_date_min = payment_qrcode_transaction[0]
                    for i in range(len(payment_qrcode_transaction)):
                        if create_date_min.create_date > payment_qrcode_transaction[i].create_date:
                            create_date_min = payment_qrcode_transaction[i]
                    for p in payment_qrcode_transaction:
                        if p.id != create_date_min.id:
                            p.unlink()
                        else:
                            if not p.pos_session_id or p.pos_session_id == '':
                                p.pos_session_id = pos_session_id

                            if not p.order_id or p.order_id == '':
                                p.order_id = order_id

                            if not p.pos_shop_id or p.pos_shop_id == '':
                                p.pos_shop_id = pos_shop_id

                            if not p.order_id.pg_order_reference or p.order_id.pg_order_reference == '':
                                p.order_id.pg_order_reference = p.pg_order_reference

                            p.state = 'checked'
                else:
                    if not payment_qrcode_transaction.pos_session_id or payment_qrcode_transaction.pos_session_id == '':
                        payment_qrcode_transaction.pos_session_id = pos_session_id

                    if not payment_qrcode_transaction.order_id or payment_qrcode_transaction.order_id == '':
                        payment_qrcode_transaction.order_id = order_id

                    if not payment_qrcode_transaction.pos_shop_id or payment_qrcode_transaction.pos_shop_id == '':
                        payment_qrcode_transaction.pos_shop_id = pos_shop_id

                    if not payment_qrcode_transaction.order_id.pg_order_reference or payment_qrcode_transaction.order_id.pg_order_reference == '':
                        payment_qrcode_transaction.order_id.pg_order_reference = payment_qrcode_transaction.pg_order_reference

                    payment_qrcode_transaction.state = 'checked'
                self.state = 'done'
            else:
                self.state = 'error'
        except Exception as ex:
            raise UserError(ex)

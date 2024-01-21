# -*- coding: utf-8 -*-

import requests.exceptions
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from requests.auth import HTTPBasicAuth
import json
import math


class CreateSInvoiceLot(models.Model):
    _name = 'create.sinvoice.lot'
    _description = 'SInvoice Lot - Logging API SInvoice'
    _order = 'id desc'

    name = fields.Char(string='Name')
    params = fields.Text(string='Params')
    params_api_get_invoice = fields.Text(string='Params Api Get Invoice')
    response = fields.Text(string='Response')
    response_api_get_invoice = fields.Text(string='Response Api Get Invoice')
    action_type = fields.Selection([
        ('release', 'Release'),
        ('cancel', 'Cancel')
    ], string='Action Type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('cancel', 'Cancel'),
        ('error', 'Error'),
        ('done', 'Done')
    ], default='draft', string='State')
    line_ids = fields.One2many(comodel_name='pos.order', inverse_name='sinvoice_lot_id', string='Orders')
    session_id = fields.Many2one('pos.session', string='Session')
    start_at = fields.Datetime(string='Start At', related='session_id.start_at')
    config_id = fields.Many2one('pos.config', string='Pos Config', related='session_id.config_id')

    def action_api_release_sinvoice(self):
        try:
            if self.state == 'draft':
                self.state = 'queue'
                self.sudo().with_delay(channel='root.action_api_sinvoice', max_retries=3)._action_done()
        except Exception as ex:
            raise ValidationError(ex)

    def _action_done(self):
        try:
            company = self.env.company
            sinvoice_type = company.sinvoice_type
            sinvoice_template_code = company.sinvoice_template_code
            sinvoice_series = company.sinvoice_series
            url = company.sinvoice_production_url + '/InvoiceAPI/InvoiceWS/createBatchInvoice/' + str(company.vat)

            headers = {
                'Content-Type': 'application/json'
            }
            payload = {
                'commonInvoiceInputs': self.prepair_data(company)
            }

            auth = requests.auth.HTTPBasicAuth(username=company.sinvoice_username, password=company.sinvoice_password)

            response = requests.request('POST', url, headers=headers, data=json.dumps(payload), auth=auth)
            res = json.loads(response.text)
            self.response = response.text
            self.params = str(payload)
            self._cr.commit()

            if response.status_code != 200:
                result = {
                    'params': payload,
                    'response': response.text,
                }
                raise ValidationError(str(result))
            else:
                if 'lstMapError' and 'totalFail' and 'totalSuccess' in res:
                    if res['totalSuccess'] > 0:
                        all_payload_get_inv = []
                        all_res_get_inv = []
                        result = []
                        for item in res['createInvoiceOutputs']:
                            # API GET INVOICE BY TRANSACTION UUID
                            url = company.sinvoice_production_url + '/InvoiceAPI/InvoiceWS/searchInvoiceByTransactionUuid'
                            headers_get_inv = {
                                'Content-Type': 'application/x-www-form-urlencoded'
                            }
                            payload_get_inv = {
                                'supplierTaxCode': str(company.vat),
                                'transactionUuid': item['transactionUuid'],
                            }
                            response_get_inv = requests.request('POST', url, headers=headers_get_inv,
                                                                data=payload_get_inv, auth=auth)
                            if response_get_inv.status_code != 200:
                                result.append({
                                    'params_get_inv': payload_get_inv,
                                    'response_get_inv': response_get_inv.text,
                                })
                                continue

                            res_get_inv = json.loads(response_get_inv.text)
                            all_payload_get_inv.append(payload_get_inv)
                            all_res_get_inv.append(response_get_inv.text)
                            order = self.env['pos.order'].search([('transaction_uuid', '=', item['transactionUuid'])])
                            if 'result' in res_get_inv:
                                _sinvoice_no = res_get_inv['result'][0]['invoiceNo']
                                if _sinvoice_no:
                                    order.sinvoice_no = _sinvoice_no
                                order.sinvoice_issued_date = datetime.fromtimestamp(
                                    int(res_get_inv['result'][0]['issueDate']) // 1000)
                                order.sinvoice_state = 'released'

                                # update account_sinvoice
                                order.sinvoice_id.sinvoice_no = order.sinvoice_no
                                order.sinvoice_id.sinvoice_state = 'released'
                                order.sinvoice_id.sinvoice_date = order.sinvoice_issued_date
                                order.sinvoice_id.order_id = order.id
                                order.sinvoice_id.sinvoice_lot_id = self.id
                                order.sinvoice_id.reservation_code = res_get_inv['result'][0]['reservationCode']
                                self._cr.commit()
                            else:
                                result.append({
                                    'params_get_inv': payload_get_inv,
                                    'response_get_inv': response_get_inv.text,
                                })
                                continue
                        self.params_api_get_invoice = all_payload_get_inv
                        self.response_api_get_invoice = all_res_get_inv
                        self._cr.commit()
                        if result:
                            raise ValidationError(result)
                    if res['totalFail'] > 0:
                        result = {
                            'params': payload,
                            'response': response.text,
                        }
                        raise ValidationError(str(result))
                    else:
                        self.state = 'done'
                else:
                    result = {
                        'params': payload,
                        'response': response.text,
                    }
                    raise ValidationError(str(result))
        except Exception as ex:
            raise ValidationError(ex)

    @api.model
    def create(self, vals):
        try:
            seq = self.env['ir.sequence'].next_by_code('tracking.sinvoice')
            vals['name'] = 'SINVOICE/' + datetime.today().strftime('%d%m%Y') + '/' + seq
            return super(CreateSInvoiceLot, self).create(vals)
        except Exception as e:
            raise ValidationError(e)

    def prepair_data(self, company):
        vals = []
        for item in self.line_ids:
            total_tax = total_amount_untax = total_amount_withtax = 0
            item.transaction_uuid = item.pos_reference
            item.sinvoice_series = self.env.company.sinvoice_series
            general_info = {
                'templateCode': company.sinvoice_template_code,
                'invoiceSeries': company.sinvoice_series,
                # 'invoiceIssuedDate': int(item.date_order.timestamp()) * 1000,
                'currencyCode': company.currency_id.name,
                'adjustmentType': '1',
                'paymentStatus': True,
                'cusGetInvoiceRight': True,
                'transactionUuid': item.pos_reference,
            }
            # Hard code phương thức thanh toán
            payments = [
                {
                    'paymentMethodName': 'TM/CK',
                }
            ]
            # Nếu có mã số thuế người mua => Người mua có lấy hoá đơn
            if item.sinvoice_vat:
                string_value = item.partner_id.name
                buyer_info = {
                    'buyerLegalName': item.sinvoice_company_name,
                    'buyerTaxCode': item.sinvoice_vat,
                    'buyerAddressLine': item.sinvoice_address,
                    'buyerEmail': item.sinvoice_email,
                    'buyerNotGetInvoice': 0
                }
            elif not item.sinvoice_vat and item.sinvoice_email:
                string_value = item.partner_id.name
                buyer_info = {
                    'buyerLegalName': item.sinvoice_company_name,
                    'buyerTaxCode': '',
                    'buyerAddressLine': item.sinvoice_address,
                    'buyerEmail': item.sinvoice_email,
                    'buyerNotGetInvoice': 0
                }
            else:
                string_value = ''
                buyer_info = {
                    'buyerNotGetInvoice': 1,
                    'buyerName': 'Khách lẻ không lấy hoá đơn',
                    'buyerLegalName': 'Khách hàng không lấy hoá đơn',
                }
            if buyer_info['buyerNotGetInvoice'] == 1:
                item.sinvoice_company_name = buyer_info['buyerLegalName']

            item_info = []
            list_order_line = []
            list_product = item.lines.filtered(lambda x: x.is_combo_line is False).product_id.ids
            for p in list_product:
                order_line_duplicate = item.lines.filtered(lambda x: x.product_id.id == p)
                # Duplicate product in order lines
                if len(order_line_duplicate) > 1:
                    # line tính tiền
                    order_line = order_line_duplicate.filtered(lambda x: x.product_id.id == p and x.price_subtotal > 0)
                    qty = price_subtotal = price_subtotal_incl = total_promotion = sinvoice_tax_amount = 0
                    # Tính tổng các sản phẩm trùng nhau
                    for k in order_line_duplicate:
                        qty += k.qty
                        price_subtotal += k.price_subtotal
                        price_subtotal_incl += k.price_subtotal_incl
                        total_promotion += (k.x_is_price_promotion + k.amount_promotion_loyalty + k.amount_promotion_total)
                        sinvoice_tax_amount += k.sinvoice_tax_amount
                    if len(order_line) > 1:
                        # case này bị tách dòng phải tính tổng thuế
                        list_order_line.append({
                            'id': order_line[0].id,
                            'full_product_name': order_line[0].full_product_name,
                            'product_id': order_line[0].product_id.id,
                            'total_promotion': total_promotion,
                            'vat': order_line[0].tax_ids_after_fiscal_position.amount,
                            'vat_include_price': order_line[0].tax_ids_after_fiscal_position.price_include,
                            'price_unit': order_line[0].price_unit,
                            'unit_name': order_line[0].product_uom_id.name,
                            'rounding_uom': order_line[0].product_uom_id.rounding,
                            'price_subtotal': price_subtotal,
                            'price_subtotal_incl': price_subtotal_incl,
                            'qty': qty,
                            'sinvoice_tax_amount': sinvoice_tax_amount
                        })
                    elif len(order_line) == 1:
                        total_promotion = order_line.x_is_price_promotion + order_line.amount_promotion_loyalty + order_line.amount_promotion_total
                        list_order_line.append({
                            'id': order_line.id,
                            'full_product_name': order_line.full_product_name,
                            'product_id': order_line.product_id.id,
                            'total_promotion': total_promotion,
                            'vat': order_line.tax_ids_after_fiscal_position.amount,
                            'vat_include_price': order_line.tax_ids_after_fiscal_position.price_include,
                            'price_unit': order_line.price_unit,
                            'unit_name': order_line.product_uom_id.name,
                            'rounding_uom': order_line.product_uom_id.rounding,
                            'price_subtotal': order_line.price_subtotal,
                            'price_subtotal_incl': order_line.price_subtotal_incl,
                            'qty': qty,
                            'sinvoice_tax_amount': order_line.sinvoice_tax_amount
                        })
                    else:
                        # tặng all
                        list_order_line.append({
                            'id': order_line_duplicate[0].id,
                            'full_product_name': order_line_duplicate[0].full_product_name,
                            'product_id': order_line_duplicate[0].product_id.id,
                            'total_promotion': total_promotion,
                            'vat': order_line_duplicate[0].tax_ids_after_fiscal_position.amount,
                            'vat_include_price': order_line_duplicate[0].tax_ids_after_fiscal_position.price_include,
                            'price_unit': order_line_duplicate[0].price_unit,
                            'unit_name': order_line_duplicate[0].product_uom_id.name,
                            'rounding_uom': order_line_duplicate[0].product_uom_id.rounding,
                            'price_subtotal': 0,
                            'price_subtotal_incl': 0,
                            'qty': qty,
                            'sinvoice_tax_amount': order_line_duplicate[0].sinvoice_tax_amount
                        })
                else:
                    total_promotion = order_line_duplicate.x_is_price_promotion + order_line_duplicate.amount_promotion_loyalty + order_line_duplicate.amount_promotion_total
                    list_order_line.append({
                        'id': order_line_duplicate.id,
                        'full_product_name': order_line_duplicate.full_product_name,
                        'product_id': order_line_duplicate.product_id.id,
                        'total_promotion': total_promotion,
                        'vat': order_line_duplicate.tax_ids_after_fiscal_position.amount,
                        'vat_include_price': order_line_duplicate.tax_ids_after_fiscal_position.price_include,
                        'price_unit': order_line_duplicate.price_unit,
                        'unit_name': order_line_duplicate.product_uom_id.name,
                        'rounding_uom': order_line_duplicate.product_uom_id.rounding,
                        'price_subtotal': order_line_duplicate.price_subtotal,
                        'price_subtotal_incl': order_line_duplicate.price_subtotal_incl,
                        'qty': order_line_duplicate.qty,
                        'sinvoice_tax_amount': order_line_duplicate.sinvoice_tax_amount
                    })

            for line in list_order_line:
                # Không lấy dòng KM
                if line['price_subtotal'] < 0 or line['full_product_name'] == 'KM':
                    continue

                # Tính giá trị làm tròn đơn vị
                rounding_uom = int(math.log10(1 / float(line['rounding_uom'])))
                #Tổng giá trị km
                total_promotion = line['total_promotion']

                # Nếu price_subtotal của sản phẩm = 0 => Là sản phẩm tặng => Thêm ghi chú
                if line['price_subtotal'] == 0 or (line['price_subtotal_incl'] - total_promotion) <= 0:
                    item_info.append({
                        'itemName': line['full_product_name'],
                        'unitName': line['unit_name'],
                        'unitPrice': 0.0,
                        'quantity': round(line['qty'], rounding_uom),
                        'taxPercentage': line['vat'],
                        'itemNote': 'Hàng khuyến mại không thu tiền'
                    })
                else:
                    vat_percent = line['vat']
                    qty = round(line['qty'], rounding_uom)
                    # Đơn giá đã bao gồm thuế
                    if line['vat_include_price']:
                        amount_with_tax = line['price_subtotal_incl'] - total_promotion
                        taxAmount = line['sinvoice_tax_amount']
                        # tổng tiền trước thuế gồm số lẻ do làm tròn
                        amount_untax_with_changed = amount_with_tax - taxAmount
                        # Đơn giá sau KM
                        unit_price = round((amount_untax_with_changed / qty), 2)
                        # tổng đơn
                        total_tax += taxAmount
                        total_amount_untax += amount_untax_with_changed
                        total_amount_withtax += amount_with_tax
                        item_info.append({
                            'itemName': line['full_product_name'],
                            'unitName': line['unit_name'],
                            'unitPrice': unit_price,
                            'quantity': qty,
                            'taxPercentage': vat_percent,
                            'taxAmount': taxAmount,
                            'itemTotalAmountWithoutTax': amount_untax_with_changed,
                            'itemTotalAmountWithTax': amount_with_tax,
                        })
                    else:
                        total_promotion = line['total_promotion']
                        unit_price = line['price_unit']
                        amount_untax = unit_price * qty
                        taxAmount = line['sinvoice_tax_amount']
                        amount_withtax = amount_untax + taxAmount - total_promotion
                        # tổng đơn
                        total_tax += taxAmount
                        total_amount_untax += amount_untax
                        total_amount_withtax += amount_withtax
                        item_info.append({
                            'itemName': line['full_product_name'],
                            'unitName': line['unit_name'],
                            'unitPrice': unit_price,
                            'quantity': qty,
                            'taxPercentage': vat_percent,
                            'taxAmount': taxAmount,
                            'itemTotalAmountWithoutTax': amount_untax,
                            'itemTotalAmountWithTax': amount_withtax,
                        })

            meta_data = [
                {
                    'id': None,
                    'keyTag': 'Customername',
                    'valueType': 'text',
                    'stringValue': string_value,
                    'keyLabel': 'Họ tên người mua hàng',
                    'isRequired': False,
                    'isSeller': False
                },
                {
                    'id': None,
                    'keyTag': 'PaymentCurency',
                    'valueType': 'text',
                    'stringValue': 'VNĐ',
                    'keyLabel': 'Đồng tiền thanh toán',
                    'isRequired': False,
                    'isSeller': False
                },
                {
                    'keyTag': 'SellerAccount',
                    'valueType': 'text',
                    'stringValue': company.res_partner_bank_id.acc_number,
                    'keyLabel': 'Số tài khoản người bán',
                    'isRequired': False,
                    'isSeller': False,
                },
                {
                    'keyTag': 'SellerBank',
                    'valueType': 'text',
                    'stringValue': company.res_partner_bank_id.bank_name,
                    'keyLabel': 'Tên ngân hàng người Bán',
                    'isRequired': False,
                    'isSeller': False,
                }
            ]

            val = {
                'generalInvoiceInfo': general_info,
                'buyerInfo': buyer_info,
                'payments': payments,
                'itemInfo': item_info,
                'metadata': meta_data,
            }
            vals.append(val)

            # Create record account_sinvoice
            acc_sinvoice_val = {
                'transaction_uuid': general_info['transactionUuid'],
                'buyer_name': buyer_info['buyerName'] if 'buyerName' in buyer_info else '',
                'buyer_tax_code': buyer_info['buyerTaxCode'] if 'buyerTaxCode' in buyer_info else '',
                'buyer_address_line': buyer_info['buyerAddressLine'] if 'buyerAddressLine' in buyer_info else '',
                'buyer_email': buyer_info['buyerEmail'] if 'buyerEmail' in buyer_info else '',
                'buyer_not_get_invoice': str(buyer_info['buyerNotGetInvoice']),
                'currency_id': self.env.user.currency_id.id,
                'amount_tax': total_tax,
                'amount_untax': total_amount_untax,
                'total_amount_tax': total_amount_withtax,
                'sinvoice_payment_method': payments[0]['paymentMethodName'],
            }
            if not item.sinvoice_id:
                account_sinvoice_obj = self.env['account.sinvoice'].create(acc_sinvoice_val)
                # Update sinvoice_id in pos_order
                item.sinvoice_id = account_sinvoice_obj.id
        return vals

    def action_api_destroy_sinvoice(self, order):
        try:
            if self.state == 'draft':
                self.state = 'queue'
                self.sudo().with_delay(channel='root.action_api_sinvoice', max_retries=3)._action_destroy(order)
        except Exception as ex:
            raise ValidationError(ex)

    def _action_destroy(self, order):
        try:
            order_origin = order.x_pos_order_refund_id
            time_now = datetime.now()
            company = self.env.company
            sinvoice_type = company.sinvoice_type
            sinvoice_template_code = company.sinvoice_template_code
            sinvoice_series = company.sinvoice_series
            url = company.sinvoice_production_url + '/InvoiceAPI/InvoiceWS/cancelTransactionInvoice'
            payload = {
                'supplierTaxCode': str(company.vat),
                'templateCode': sinvoice_template_code,
                'invoiceNo': order_origin.sinvoice_no,
                'strIssueDate': int(order_origin.sinvoice_issued_date.timestamp()) * 1000,
                'additionalReferenceDesc': order.name,
                'additionalReferenceDate': int(order.date_order.timestamp()) * 1000,
                'reasonDelete': order.x_note_return or '',
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            auth = requests.auth.HTTPBasicAuth(username=company.sinvoice_username, password=company.sinvoice_password)
            response = requests.request('POST', url, headers=headers, data=payload, auth=auth)
            res = json.loads(response.text)
            self.response = str(response.text)
            self.params = payload
            self.session_id = order.session_id
            self._cr.commit()
            if 'errorCode' in res and not res['errorCode']:
                self.state = 'done'
                order_origin.sinvoice_state = 'cancel_release'
                order_origin.sinvoice_id.sinvoice_state = 'cancel_release'
                order_origin.sinvoice_id.sinvoice_cancel_date = order.date_order
                self._cr.commit()
            else:
                result = {
                    'params': payload,
                    'response': response.text
                }
                raise ValidationError(str(result))
        except Exception as ex:
            raise ValidationError(ex)

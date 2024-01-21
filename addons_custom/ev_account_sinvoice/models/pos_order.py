# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
from datetime import datetime, timedelta
import json
import logging


class PosOrder(models.Model):
    _inherit = 'pos.order'

    sinvoice_id = fields.Many2one('account.sinvoice', string='Account SInvoice', copy=False)
    sinvoice_lot_id = fields.Many2one('create.sinvoice.lot', string='Create SInvoice Lot', copy=False)
    sinvoice_no = fields.Char(string='SInvoice No', size=15, copy=False,
                              help='Invoice No (eg: K23TAA00000001, K23TAA: invoice symbol, 00000001: incre number)')
    sinvoice_series = fields.Char(string='SInvoice Series', size=20, help='Invoice symbol, eg: K23TAA', copy=False)
    sinvoice_issued_date = fields.Datetime(string='SInvoice Issued Date', help='Invoice issued date', copy=False)
    sinvoice_state = fields.Selection([
        ('no_release', 'No Release'),
        ('released', 'Released'),
        ('queue', 'Queue'),
        ('cancel_release', 'Cancel Release')
    ], string='SInvoice State', copy=False)

    sinvoice_vat = fields.Char(string='SInvoice VAT', size=20, copy=False)
    sinvoice_company_name = fields.Char(string='SInvoice Company Name', size=1200, copy=False)
    sinvoice_address = fields.Char(string='SInvoice Address', size=1200, copy=False)
    sinvoice_email = fields.Char(string='SInvoice Email', size=1200, copy=False)
    transaction_uuid = fields.Char(string='Transaction Uuid', copy=False, index=True)

    def get_partner_info_sinvoice(self, partner_id):
        sql = """
            SELECT sinvoice_vat,
                   sinvoice_company_name,
                   sinvoice_address,
                   sinvoice_email
            FROM pos_order po
            WHERE po.partner_id = %s
            AND (po.sinvoice_state = 'released' OR po.sinvoice_state = 'cancel_release')
            AND po.sinvoice_vat IS NOT NULL
            AND po.sinvoice_vat != ''
            ORDER BY po.id DESC
            LIMIT 1;
        """
        self._cr.execute(sql % int(partner_id))
        res = self._cr.dictfetchall()
        if len(res) > 0:
            return res[0]
        return None

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['sinvoice_vat'] = str(ui_order.get('x_sinvoice_vat'))
        res['sinvoice_company_name'] = str(ui_order.get('x_sinvoice_company_name'))
        res['sinvoice_address'] = str(ui_order.get('x_sinvoice_address'))
        res['sinvoice_email'] = str(ui_order.get('x_sinvoice_email'))
        return res

    @api.model
    def write(self, vals):
        res = super(PosOrder, self).write(vals)
        if 'state' in vals and vals[
            'state'] == 'paid' and self.x_allow_return == True and self.x_pos_order_refund_id != None:
            order_original = self.env['pos.order'].search([('id', '=', self.x_pos_order_refund_id.id)])
            if order_original and order_original.sinvoice_state == 'released':
                val = {
                    'action_type': 'cancel',
                    'line_ids': self
                }
                create_sinvoice_lot = self.env['create.sinvoice.lot'].create(val)
                create_sinvoice_lot.action_api_destroy_sinvoice(self)
        return res

    def action_api_destroy_sinvoice(self):
        try:
            order_origin = self.x_pos_order_refund_id
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
                'additionalReferenceDesc': self.name,
                'additionalReferenceDate': int(self.date_order.timestamp()) * 1000,
                'reasonDelete': self.x_note_return or '',
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            auth = requests.auth.HTTPBasicAuth(username=company.sinvoice_username, password=company.sinvoice_password)
            response = requests.request('POST', url, headers=headers, data=payload, auth=auth)
            res = json.loads(response.text)
            if 'errorCode' in res and not res['errorCode']:
                order_origin.sinvoice_state = 'cancel_release'
                order_origin.sinvoice_id.sinvoice_state = 'cancel_release'
                order_origin.sinvoice_id.sinvoice_cancel_date = self.date_order
                self._cr.commit()
            else:
                result = {
                    'params': payload,
                    'response': response.text
                }
                raise ValidationError(str(result))
        except Exception as ex:
            raise ValidationError(ex)

    def action_update_invoice_no(self):
        time_now = datetime.now() + timedelta(hours=7) - timedelta(days=1)
        time_compare = datetime(time_now.year, time_now.month, time_now.day).strftime('%Y-%m-%d')
        
        sql = """
            SELECT id FROM pos_order
            WHERE (date_order + INTERVAL '7 hours')::date = '%s'
             AND sinvoice_state = 'released'
             AND sinvoice_no IS NULL OR sinvoice_no  = ''
        """
        self._cr.execute(sql % (time_compare))
        orders = self._cr.dictfetchall()

        company = self.env.company
        url = company.sinvoice_production_url + '/InvoiceAPI/InvoiceWS/searchInvoiceByTransactionUuid'
        auth = requests.auth.HTTPBasicAuth(username=company.sinvoice_username,
                                           password=company.sinvoice_password)
        header = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        for item in orders:
            order = self.env['pos.order'].search([('id', '=', item['id'])])
            if order.sinvoice_state == 'released':
                payload = {
                    'supplierTaxCode': str(company.vat),
                    'transactionUuid': order.pos_reference
                }
                response = requests.request('POST', url, headers=header, data=payload, auth=auth)
                if response.status_code != 200:
                    continue
                res = json.loads(response.text)
                if 'result' in res:
                    order.sinvoice_no = res['result'][0]['invoiceNo']
                    order.sinvoice_issued_date = datetime.fromtimestamp(
                        int(res['result'][0]['issueDate']) // 1000)
                    order.sinvoice_state = 'released'
                    # update account_sinvoice
                    order.sinvoice_id.sinvoice_no = order.sinvoice_no
                    order.sinvoice_id.sinvoice_state = 'released'
                    order.sinvoice_id.sinvoice_date = order.sinvoice_issued_date
                    order.sinvoice_id.order_id = order.id
                    order.sinvoice_id.reservation_code = res['result'][0]['reservationCode']

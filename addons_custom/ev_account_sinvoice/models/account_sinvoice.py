# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError


class AccountEInvoice(models.Model):
    _name = 'account.sinvoice'
    _description = 'Account SInvoice'
    _rec_name = 'sinvoice_no'
    _order = 'id desc'

    sinvoice_no = fields.Char(string='SInvoice No', size=15, help='Invoice No (eg: K23TAA00000001, K23TAA: invoice symbol, 00000001: incre number)')
    sinvoice_state = fields.Selection([
        ('no_release', 'No Release'),
        ('released', 'Released'),
        ('queue', 'Queue'),
        ('cancel_release', 'Cancel Release')
    ], default='no_release', string='SInvoice State')
    sinvoice_date = fields.Datetime(string='SInvoice Date')
    sinvoice_payment_method = fields.Char(string='SInvoice Payment')
    buyer_name = fields.Char(string='Buyer Name', size=800, help='Buyer name in case of retail or individual buyers. Buyer or unit name is required when buyer_not_get_invoice = 0')
    buyer_code = fields.Char(string='Buyer Code', size=400)
    buyer_tax_code = fields.Char(string='Buyer Tax Code', size=20, help='Required when buyer_not_get_invoice = 0')
    buyer_address_line = fields.Char(string='Buyer Address Line', size=1200, help='Required when buyer_not_get_invoice = 0')
    buyer_email = fields.Char(string='Buyer Email', size=50)
    buyer_bank_name = fields.Char(string='Buyer Bank Name', size=200)
    buyer_bank_account = fields.Char(string='Buyer Bank Account', size=100)
    buyer_id_type = fields.Selection([
        ('identify_card', 'Identity Card Number'),
        ('passport', 'Passport'),
        ('registration_cer', 'Registration Certificate')
    ], string='Buyer Id Type')
    buyer_id_no = fields.Char(string='Buyer Id No', help='Buyer document number, can be identity card, business license, passport')
    buyer_not_get_invoice = fields.Selection([
        ('0', 'Buyer take invoice'),
        ('1', 'Buyer does not take invoice')
    ], default='0', string='Buyer Not Get Invoice')
    currency_id = fields.Many2one('res.currency', string='Currency')
    sinvoice_cancel_date = fields.Datetime(string='SInvoice Cancel Date')
    amount_untax = fields.Float(string='Amount Untax', help='Total pre-tax money')
    amount_tax = fields.Float(string='Amount Tax', help='Total amount of tax')
    total_amount_tax = fields.Float(string='Total Amount Tax', help='Total amount after tax')
    transaction_uuid = fields.Char(string='Transaction Uuid', index=True)
    order_id = fields.Many2one('pos.order', string='Pos Order')
    sinvoice_lot_id = fields.Many2one('create.sinvoice.lot', string='Lot/Serial')
    reservation_code = fields.Char(string='Reservation Code')

    def get_url_check_vat(self):
        try:
            url_check_vat = self.env['ir.config_parameter'].sudo().get_param('url_check_vat')
            if not url_check_vat:
                return None
            return url_check_vat
        except Exception as ex:
            raise ValidationError(ex)

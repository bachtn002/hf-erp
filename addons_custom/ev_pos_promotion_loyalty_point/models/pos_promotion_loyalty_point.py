# -*- coding: utf-8 -*-
import json

import requests
from odoo import _, models, api, fields
from odoo.exceptions import UserError, ValidationError
from werkzeug.urls import url_encode

class PosPromotionLoyaltyPoint(models.Model):
    _name = 'pos.promotion.loyalty.point'
    _description = 'PosPromotionLoyaltyPoint'

    promotion_id = fields.Many2one(comodel_name='pos.promotion',
                                   string='Promotion')
    total_amount = fields.Float(digits=(18, 2),
                                string='Total Amount',
                                help=_('Total amount of order'))
    loyalty_point = fields.Float(digits=(18, 2),
                            string='Loyalty Point')

    @api.constrains('total_amount')
    def check_total_amount(self):
        for rc in self:
            if rc.total_amount <= 0:
                raise UserError(_('You can only create total amount > 0'))

    @api.constrains('loyalty_point')
    def check_discount(self):
        for rc in self:
            if rc.loyalty_point <= 0:
                raise UserError(_('You can only create loyalty point > 0'))

    def check_partner(self, authorization):
        try:
            base_url = self.env['ir.config_parameter'].sudo().get_param('url_api_verify_barcode')
            token = self.env['ir.config_parameter'].sudo().get_param('TOKEN-VERIFY-BARCODE-API')
            url = base_url + '/api/v1/services/customer/verify-barcode'
            header = {
                'Content-Type': 'application/json',
                'Authorization': token,
            }
            data = {"token": authorization}
            response = requests.get(url, params=url_encode(data), headers=header, verify=False)
            response_json = response.json()
            if response_json['error'] != '200':
                return False
            else:
                phone = response_json['data']['mobile']
                if not phone:
                    return False
                partner_id = self.env['res.partner'].search([('phone', '=', phone)], limit=1)
                if not partner_id:
                    partner_id = self.env['res.partner'].create({
                        'name': response_json['data']['name'],
                        'phone': response_json['data']['mobile']
                    })
                return str(partner_id.phone)
        except Exception as e:
            raise e

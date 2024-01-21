# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError
import ast
import json
import requests


class SyncStateMiniapp(models.Model):
    _name = 'sync.state.miniapp'
    _description = 'Update State Shipping Order'
    _order = 'id desc'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='draft', string='State')
    message = fields.Char(string='Message')
    params = fields.Text(string='Params')
    response = fields.Text(string='Response')

    def action_update_status_shipping(self):
        try:
            if self.state == 'draft':
                self.state = 'queue'
                self.sudo().with_delay(channel='root.action_update_status_shipping',
                                       max_retries=3)._action_update_status_shipping()
        except Exception as ex:
            raise ValidationError(ex)

    def _action_update_status_shipping(self):
        payload = ast.literal_eval(self.params)
        url = self.env['ir.config_parameter'].sudo().get_param('url_api_verify_barcode') + '/api/v1/services/order/update-status'
        token = self.env['ir.config_parameter'].sudo().get_param('TOKEN-VERIFY-BARCODE-API')
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }
        response = requests.request('POST', url, headers=headers, data=json.dumps(payload))
        self.response = response.text
        result = json.loads(response.text)
        if result['error'] == '404':
            self.state = 'error'
            self.message = result['message']
        elif result['error'] == '406':
            self.state = 'error'
            self.message = result['message']
        elif result['error'] == '200':
            self.state = 'done'
            self.message = result['message']
        else:
            self.state = 'error'
            self.message = '500'

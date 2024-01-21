# -*- coding: utf-8 -*-

import ast

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WebhookAha(models.Model):
    _name = 'webhook.aha'
    _description = 'Data Webhook aha'
    _order = 'create_date desc'

    data = fields.Text('Data')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queue', 'Queue'),
        ('done', 'Done')],
        'State', default='draft')

    def action_confirm(self):
        try:
            if self.state == 'draft':
                self.state = 'queue'
                self.sudo().with_delay(channel='root.action_send_delivery', max_retries=3)._action_done()
        except Exception as e:
            raise ValidationError(e)

    def _action_done(self):
        try:
            json_data = ast.literal_eval(self.data)
            delivery_reference = json_data.get('_id')
            phone = json_data.get('supplier_id')
            driver_name = json_data.get('supplier_name')
            status = json_data.get('status')
            sub_status = json_data.get('path')[1].get('status') if json_data.get('path')[1] else ''
            status_type = json_data.get('sub_status') if json_data.get('sub_status') else ''
            delivery_id = self.env['delivery.management'].sudo().search(
                [('delivery_reference', '=', delivery_reference)], limit=1)
            if delivery_id:
                delivery_id.driver_name = driver_name
                delivery_id.driver_phone = phone
                delivery_id.license_plate = phone
                state = delivery_id.set_state_ahamove(status, sub_status, status_type)
                if delivery_id.state != state:
                    delivery_id.state = state
                delivery_id.state_delivery = status_type + ' | ' + status + ' | ' + sub_status
            self.state = 'done'
        except Exception as e:
            raise ValidationError(e)

    def delete_webhook_aha(self):
        try:
            query = """
                DELETE FROM webhook_aha where state = 'done'; 
            """
            self.env.cr.execute(query)
            self.env.cr.commit()
        except Exception as e:
            raise ValidationError(e)

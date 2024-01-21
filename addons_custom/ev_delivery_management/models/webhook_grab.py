# -*- coding: utf-8 -*-
import ast

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WebhookGrab(models.Model):
    _name = 'webhook.grab'
    _description = 'Data Webhook Grab'
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
            params = ast.literal_eval(self.data)
            delivery_id = self.env['delivery.management'].sudo().search(
                [('name', '=', params.get('merchantOrderID'))], limit=1)
            if delivery_id:
                delivery_id.state_delivery = params.get('status')
                delivery_id.track_url = params.get('trackURL')
                delivery_id.pickup_pin = params.get('pickupPin')
                delivery_id.driver_name = params.get('driver').get('name') if params.get('driver') else None
                delivery_id.driver_phone = params.get('driver').get('phone') if params.get('driver') else None
                delivery_id.license_plate = params.get('driver').get('licensePlate') if params.get('driver') else None
                delivery_id.failed_reason = params.get('failedReason')
                if params.get('status') == 'PICKING_UP' and delivery_id.state != 'pickup':
                    delivery_id.state = 'pickup'
                if params.get('status') == 'IN_DELIVERY' and delivery_id.state != 'delivering':
                    delivery_id.state = 'delivering'
                if params.get('status') in ('COMPLETED', 'RETURNED') and delivery_id.state != 'done':
                    delivery_id.state = 'done'
                if params.get('status') == 'FAILED' and delivery_id.state != 'failed':
                    delivery_id.state = 'failed'
                    # delivery_id.failed_reason = params['failedReason'] if 'failedReason' in params else ''
                # if params.get('status') == 'RETURNED' and delivery_id.state != 'received':
                #     delivery_id.state = 'received'
                if params.get('status') == 'ALLOCATING' and delivery_id.state != 'waiting':
                    delivery_id.state = 'waiting'
                    delivery_id.driver_name = None
                    delivery_id.driver_phone = None
                    delivery_id.license_plate = None
                    delivery_id.track_url = None
            self.state = 'done'
        except Exception as e:
            raise ValidationError(e)

    def delete_webhook_grab(self):
        try:
            query = """
                DELETE FROM webhook_grab where state = 'done'; 
            """
            self.env.cr.execute(query)
            self.env.cr.commit()
        except Exception as e:
            raise ValidationError(e)

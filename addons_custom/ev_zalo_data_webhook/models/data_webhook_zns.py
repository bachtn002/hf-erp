# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DataWebhookZNS(models.Model):
    _inherit = 'data.webhook.zns'

    # sửa thông tin webhook để chặn khách hàng requests 1 thông tin nhiều lần
    event_name = fields.Char('Event Name', index=True)
    app_id = fields.Char('App ID', index=True)
    oa_id = fields.Char('OA ID', index=True)
    zalo_id = fields.Char('Zalo ID', index=True)
    msg_text = fields.Char('Msg Text', index=True)
    msg_id = fields.Char('Msg ID', index=True)
    tracking_id = fields.Char('Tracking ID', index=True)
    date = fields.Datetime('Date Request', index=True)

    def _action_done(self):
        try:
            if not self.msg_text:
                return super(DataWebhookZNS, self)._action_done()

            webhook_dt = self.env['data.webhook.zns'].sudo().search(
                [('app_id', '=', self.app_id), ('oa_id', '=', self.oa_id), ('zalo_id', '=', self.zalo_id),
                 ('msg_text', '=', self.msg_text), ('state', '!=', 'done'), ('create_date', '>', self.create_date)])

            if webhook_dt:
                self.state = 'done'
                return
            return super(DataWebhookZNS, self)._action_done()
        except Exception as e:
            raise ValidationError(e)

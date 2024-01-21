# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ZaloOfficialAccount(models.Model):
    _name = 'zalo.official.account'
    _description = 'Zalo Official Account Management'
    _order = 'create_date desc'

    name = fields.Char('Name OA', required=True)
    app_id = fields.Char('App ID', required=True)
    secret_key = fields.Char('Secret Key', required=True)
    active = fields.Boolean('Active', default=True)
    quota_date = fields.Date('Date Quota')
    remaining_quota = fields.Integer('Remaining Quota')
    # oa_id = fields.Char('OA ID', required=True)

    def send_message_mail(self):
        try:
            email_send = self.env['fetchmail.server'].sudo().search([('state', '=', 'done')],
                                                                    order='create_date desc', limit=1)
            if email_send:
                subject = 'ADMIN Công ty Cổ phần Quốc tế Homefarm thông báo'
                email_values = {
                    'email_to': email_send.user,
                    # 'email_from': email_send,
                    'subject': subject,
                }
                template = self.env.ref('ev_zalo_notification_service.mail_access_token_zalo')
                template.send_mail(self.id, force_send=True, raise_exception=False,
                                   email_values=email_values)
        except Exception as e:
            raise ValidationError(e)

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class CCPNotification(models.Model):
    _name = 'res.notification'
    _description = 'Notification management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    type = fields.Selection([('viber', 'Viber'), ('web', 'Web'), ('email', 'Email')], string="Message Type",
                            track_visibility='onchange')
    message = fields.Char(string="Message", track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', string="Viber Receiver", track_visibility='onchange')
    user_id = fields.Many2one('res.user', string="Receiver", track_visibility='onchange')
    web_receiver_id = fields.Many2one('res.partner', string="Web Receiver", track_visibility='onchange')
    sent_datetime = fields.Datetime(string="Sent Datetime", track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('exception', 'Exception'),
        ('received', 'Received'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string="State", track_visibility='onchange', default='draft')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    model = fields.Char('Model')
    item_id = fields.Integer('Item ID')
    mail_id = fields.Many2one('mail.activity', 'Mail')

    def action_send_message(self):
        if self.type == 'viber':
            _logger.info(f"Action Send Viber: employee: {self.employee_id.name}, phone: {self.employee_id.phone},"
                         f"notification: {self.id}")
            self.action_send_viber()
        if self.type == 'web':
            _logger.info(f"Action Send Activity: employee: {self.employee_id.name}, phone: {self.employee_id.phone},"
                         f"notification: {self.id}")
            self.action_send_web()

    def action_send_viber(self):
        from addons_custom.ev_viber_client.controllers.viber_object import async_send_viber_message
        async_send_viber_message([self.employee_id.x_viber_id.viber_uid], self.message)
        self.sent_datetime = fields.Datetime.now()
        self.state = 'received'
        _logger.info("Action Send Viber: successfully")

    def action_send_web(self):
        Mail = self.env['mail.activity'].sudo()
        res_model_id = self.env['ir.model'].search([('model', '=', self.model)]).id
        argvs = {
            'activity_type_id': 6,
            'user_id': self.user_id.id,
            'recommended_activity_type_id': False,
            'previous_activity_type_id': False,
            'summary': self.message,
            'note': ' ',
            'res_model_id': res_model_id,
            'activity_category': 'default',
            'res_id': self.item_id
        }
        mail_id = Mail.create(argvs)
        self.mail_id = mail_id.id
        self.sent_datetime = fields.Datetime.now()
        self.state = 'received'
        _logger.info("Action Send Activity: successfully")

    def action_done_web(self):
        if self.mail_id:
            self.mail_id.unlink()
            self.state = 'done'
            _logger.info("Action Send Activity: Done")

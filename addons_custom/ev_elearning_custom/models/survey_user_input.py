# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, exceptions, fields, models, _


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    x_date_expired = fields.Date(string='Date Expired', store=True,
                                 compute='_compute_date_expired')
    x_certificate_state = fields.Selection([
        ('available', 'Available'),
        ('expired', 'Expired')
    ], string='State')
    scoring_success = fields.Boolean('Quizz Passed',
                                     compute='_compute_scoring_success_custom',
                                     store=True, compute_sudo=True)

    @api.depends("scoring_success")
    def _compute_date_expired(self):
        for user_input in self:
            if user_input.scoring_success:
                months = user_input.survey_id.x_certificate_duration
                user_input.x_date_expired = user_input.create_date + relativedelta(
                    months=months)
                user_input.x_certificate_state = 'available' if user_input.x_date_expired >= date.today() else 'expired'
            else:
                user_input.x_date_expired = False
                user_input.x_certificate_state = False

    def _state_expired_certificated(self):
        user_inputs = self.env['survey.user_input'].sudo().search([
            ('x_certificate_state', '!=', 'expired'),
            ('x_date_expired', '<', datetime.today())
        ])
        user_inputs_to_exp = self.env['survey.user_input'].sudo().search([
            ('x_certificate_state', '!=', 'expired'),
            ('x_date_expired', '=', datetime.today() + timedelta(days=3))
        ])
        for user in user_inputs_to_exp:
            self._auto_send_mail_notify_exp(user)

        for user in user_inputs:
            user.write({'x_certificate_state': 'expired'})

    def _auto_send_mail_notify_exp(self, user):
        new_user = self.env['survey.user_input'].sudo().create({
            'survey_id': user.survey_id.id,
            'email': user.email,
            'partner_id': user.partner_id.id,
        }).id
        x_date_expired = {'x_date_expired': user.x_date_expired}
        self.env.ref(
            'ev_elearning_custom.email_notify_exp_certificated_template').with_context(x_date_expired).send_mail(
            new_user, notif_layout="mail.mail_notification_light",force_send=True)

    @api.depends('scoring_percentage')
    def _compute_scoring_success_custom(self):
        for user_input in self:
            user_input.scoring_success = user_input.scoring_percentage >= user_input.survey_id.scoring_success_min



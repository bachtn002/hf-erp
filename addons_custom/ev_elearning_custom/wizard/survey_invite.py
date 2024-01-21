# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    def _send_mail(self, answer):
        mail = super(SurveyInvite, self)._send_mail(answer)
        mail.send()

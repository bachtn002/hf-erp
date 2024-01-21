# -*- coding: utf-8 -*-

import codecs
import tempfile
from datetime import datetime
import xlrd
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class WizardDownloadImport(models.TransientModel):
    _name = 'wizard.download.import.template'

    file_name = fields.Binary('File', required=True)
    template_answer_file_url = fields.Char(default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
        'web.base.url') + '/ev_helpdesk/static/xlsx/import_answer.xlsx', string='Template Answer URL')

    template_question_file_url = fields.Char(default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
        'web.base.url') + '/ev_helpdesk/static/xlsx/import_question.xlsx', string='Template Question URL')

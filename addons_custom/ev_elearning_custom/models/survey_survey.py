# -*- coding: utf-8 -*-
import base64

import xlrd

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError, UserError

from odoo.osv import osv
from datetime import datetime


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    x_certificate_duration = fields.Float(string='Certificate Duration',
                                          store=True)

    x_field_binary_import_question_answer = fields.Binary(
        string="Field Binary Import")
    x_field_binary_name_question_answer = fields.Char(
        string="Field Binary Name")
    scoring_success_min = fields.Float('Success %', default=80.0, tracking=True)

    def download_template_question_answer(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_elearning_custom/static/xlsx/mau_nhap_cau_hoi.xlsx',
            "target": "_parent",
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith(
                '.xlsx') == False:
            return False
        return True

    def action_import_question_answer(self):
        try:
            if not self._check_format_excel(
                    self.x_field_binary_name_question_answer):
                raise ValidationError(_(
                    "File not found or not right format. Please check format file .xls or .xlsx"))
            data = base64.decodebytes(
                self.x_field_binary_import_question_answer)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            data_sheet = self._get_data_from_sheet(sheet)
            self._create_question_answer(data_sheet=data_sheet)

        except ValueError as e:
            raise osv.except_osv("Warning!", e)

    def _get_data_from_sheet(self, sheet):
        index = 1
        data = []
        while index < sheet.nrows:
            title = sheet.cell(index, 0).value
            is_page = sheet.cell(index, 1).value
            question_type = sheet.cell(index, 2).value
            constr_mandatory = sheet.cell(index, 3).value
            answer_score = sheet.cell(index, 5).value
            answer_date, answer_datetime, answer_numerical_box = None, None, None
            question_answer = []
            # Validation title
            if title == '':
                raise ValidationError(_(
                    "'Title' field cannot be empty in row %s") % str(index + 1))

            # Insert session
            if is_page == 1:
                data.append({
                    'title': title,
                    'is_page': True,
                })
                index = index + 1
                continue

            # Validation question_type , answer for type date, datetime, numerical_box
            if question_type not in ('date', 'datetime', 'numerical_box',
                                     'simple_choice', 'multiple_choice',
                                     'char_box', 'text_box'):
                raise ValidationError(_(
                    "Invalid value question_type field in row %s") % str(
                    index + 1))

            try:
                if question_type == 'date':
                    answer_date = datetime.strptime(sheet.cell(index, 4).value,
                                                    '%d/%m/%Y').date()
                if question_type == 'datetime':
                    answer_datetime = datetime.strptime(
                        sheet.cell(index, 4).value, '%d/%m/%Y %H:%M:%S')
                if question_type == 'numerical_box':
                    answer_numerical_box = float(sheet.cell(index, 4).value)
            except:
                raise ValidationError(_(
                    "Invalid value answer column in row %s") % str(index + 1))

            # Validation choice for question type simple choice or multichoice
            if question_type in ('simple_choice', 'multiple_choice'):
                while index < sheet.nrows:
                    if sheet.cell(index, 6).value == '':
                        raise ValidationError(_(
                            "Invalid 'choice answer' field in row %s") % str(
                            index + 1))

                    if sheet.cell(index, 7).value not in (1, 0):
                        raise ValidationError(_(
                            "Invalid 'is_correct' field in row %s") % str(
                            index + 1))
                    
                    # if sheet.cell(index, 7).value == 0 and sheet.cell(index, 8).value not in (0, ''):
                    #     raise ValidationError(_(
                    #         "Invalid value answer_score row %s") % str(
                    #         index + 1))

                    try:
                        question_answer.append({
                            'value': sheet.cell(index, 6).value,
                            'is_correct': sheet.cell(index, 7).value == 1,
                            'answer_score': float(
                                sheet.cell(index, 8).value) if sheet.cell(index, 8).value != '' else 0,
                        })
                    except:
                        raise ValidationError(_(
                            "Invalid value selection answer in row %s") % str(
                            index + 1))

                    if index + 1 < sheet.nrows and sheet.cell(index + 1, 0).value == '':
                        index = index + 1
                    else:
                        break

            try:
                question = {
                    'title': title,
                    'question_type': question_type,
                    'constr_mandatory': constr_mandatory,
                    'answer_date': answer_date,
                    'answer_datetime': answer_datetime,
                    'answer_numerical_box': answer_numerical_box,
                    'answer_score': float(
                        answer_score) if answer_score != '' else 0,
                    'question_answer': question_answer
                }
            except:
                raise ValidationError(_(
                    "Invalid value in row %s") % str(index + 1))

            data.append(question)
            index = index + 1
        return data

    def _create_question_answer(self, data_sheet):
        for question in data_sheet:
            # add session
            if len(question) == 2:
                self.env['survey.question'].create({
                    'survey_id': self.id,
                    'title': question['title'],
                    'is_page': question['is_page'] or None
                })
            else:
                # add question
                new_question = self.env['survey.question'].create({
                    'survey_id': self.id,
                    'title': question['title'],
                    'question_type': question['question_type'],
                    'constr_mandatory': question['constr_mandatory'],
                    'answer_date': question['answer_date'],
                    'answer_numerical_box': question['answer_numerical_box'],
                    'answer_score': question['answer_score'],
                }).id

                if question['question_type'] in (
                'simple_choice', 'multiple_choice'):
                    for answer in question['question_answer']:
                        self.env['survey.question.answer'].create({
                            'question_id': new_question,
                            'value': answer['value'],
                            'is_correct': answer['is_correct'],
                            'answer_score': answer['answer_score']
                        })

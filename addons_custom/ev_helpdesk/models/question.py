# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Question(models.Model):
    _name = 'question.question'
    _description = 'Question'
    _order = 'create_date desc'

    name = fields.Char('Question', required=True)
    question_code = fields.Char('Question code')
    answer_detail = fields.Text('Answer detail')

    is_question_root = fields.Boolean("Is question root")
    department_request_ids = fields.Many2many('helpdesk.department', 'department_question_rel', 'department_id', 'question_id', "Department request")
    question_tags = fields.Many2many('helpdesk.tag', 'question_tag_rel', 'question_id', 'tag_id', 'Question Tags',
                                     required=True)
    answer_ids = fields.One2many('answer.answer', 'main_question_id', string="Main question's Answer")
    error_image = fields.Binary('Error Image', help="Allowed formats: jpg, pdf, png. Maximum allowed size: 2MB.")
    error_image_filename = fields.Char()

    # name_url = fields.Char('Name Url')

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', 'The question already exists in the system!')
    # ]

    # @api.constrains('name')
    # def _constrains_name_url(self):
    #     try:
    #         for rc in self:
    #             if rc.name:
    #                 name = ' '.join(re.sub(r'[^a-zA-Z0-9 ]', '', unidecode.unidecode(rc.name).lower()).split())
    #                 rc.name_url = name.replace(' ', '-')
    #     except Exception as e:
    #         raise ValidationError(e)

    def search_question(self, search):
        try:
            question = self.env['question.question'].sudo().search(
                ['|', ('name', 'ilike', search), ('question_tags.name', 'ilike', search)])
            return question
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def get_root_question(self):
        """
        get root question based on helpdesk department applied
        """
        root_question = self.env['question.question'].search(
            [('is_question_root', '=', True), ('department_request_ids.user_ids', 'in', self.env.uid)], limit=1).id
        print(root_question)
        return root_question or False

    def create_question_rating(self, rating_value, feedback):
        model_id = self.env['ir.model']._get('question.question').id
        # created_rating = self.env['rating.rating'].search([('res_model_id', '=', model_id), ('res_id', '=', self.id),
        #                                                    ('partner_id', '=', self.env.user.partner_id.id)])

        self.env['rating.rating'].create({
            'res_model_id': model_id,
            'res_id': self.id,
            # 'rated_partner_id': self.env.user.partner_id.id,
            'partner_id': self.env.user.partner_id.id,
            'rating': rating_value,
            'feedback': feedback,
        })

from odoo import models, fields, _


class Answer(models.Model):
    _name = 'answer.answer'
    _description = 'Answer'

    name = fields.Char("Answer name", required=1)
    answer_code = fields.Char('Answer code')

    main_question_id = fields.Many2one('question.question', string="Main Question", required=1)
    next_question_id = fields.Many2one('question.question', string="Next Question")
    helpdesk_department_id = fields.Many2one('helpdesk.department', string="Helpdesk Department")

    answer_detail = fields.Text('Answer detail')
    error_image = fields.Binary('Error Image', help="Allowed formats: jpg, pdf, png. Maximum allowed size: 2MB.")
    error_image_filename = fields.Char()

    name_url = fields.Char('Name Url')
    page_end_redirect = fields.Selection(string="Page end redirect", selection=[('create_ticket', 'Create ticket'), ('rating_page', 'Rating page'), ])

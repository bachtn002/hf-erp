# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, MissingError, UserError
from odoo import http
from odoo.http import request


class QuestionController(http.Controller):

    @http.route([
        '/my/help_custom/create_ticket',
        '/my/help_custom/create_ticket/<int:answer_id>',
    ], type='json', auth="user", website=True)
    def create_ticket(self, answer_id=None):
        last_question = request.env['answer.answer'].browse(answer_id)
        helpdesk_department_id = last_question.helpdesk_department_id
        app_support = request.env['app.support'].sudo().search([])
        ticket_type = request.env['helpdesk.ticket.type'].sudo().search(
            [('x_helpdesk_department_id', 'in', helpdesk_department_id.ids)])
        if (len(request.env.user.x_pos_shop_ids) == 1):
            pos_shop_code = request.env.user.x_pos_shop_ids[0].code
        else:
            pos_shop_code = ""
        vals = {
            'helpdesk_department': helpdesk_department_id,
            'phone': request.env.user.partner_id.phone or '',
            'email': request.env.user.partner_id.email or '',
            'app_support': app_support,
            'ticket_type': ticket_type,
            'pos_shop_code': pos_shop_code,
        }
        return http.request.env['ir.ui.view']._render_template("ev_helpdesk.ticket_submit_form",
                                                               vals)

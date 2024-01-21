from markupsafe import Markup

from odoo import http, _, fields
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from dateutil import relativedelta
import datetime
from operator import itemgetter
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
# from odoo.addons.helpdesk.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal


class QuestionController(CustomerPortal):

    @http.route([
        "/helpdesk/ticket/<int:ticket_id>",
        "/helpdesk/ticket/<int:ticket_id>/<access_token>",
        '/my/ticket/<int:ticket_id>',
        '/my/ticket/<int:ticket_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def tickets_followup(self, ticket_id=None, access_token=None, **kw):
        # check time allow to set back to draft not over 3 days
        try:
            ticket_sudo = self._document_check_access('helpdesk.ticket', ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        max_days = request.env['ir.config_parameter'].sudo().get_param('ev_helpdesk.days_allow_back_to_new_ticket')
        if ticket_sudo.close_date:
            if max_days:
                if ticket_sudo.close_date + relativedelta.relativedelta(days=int(max_days)) >= datetime.datetime.now():
                    ticket_sudo.x_allow_set_back_draft = True
                else:
                    ticket_sudo.x_allow_set_back_draft = False
            else:
                raise UserError(_("There is no config days can reverse ticket stage!"))
        values = self._ticket_get_page_view_values(ticket_sudo, access_token, ** kw)
        return request.render("helpdesk.tickets_followup", values)

    @http.route([
        '/my/help_custom/create_ticket',
        '/my/help_custom/create_ticket/<int:answer_id>',
    ], type='json', auth="user", website=True)
    def create_ticket(self, answer_id=None):
        # teams = request.env['helpdesk.team'].sudo().search([])
        last_question = request.env['answer.answer'].browse(answer_id)
        helpdesk_department_id = last_question.helpdesk_department_id
        app_support = request.env['app.support'].sudo().search([])
        ticket_type = request.env['helpdesk.ticket.type'].sudo().search([])
        if(len(request.env.user.x_pos_shop_ids) == 1):
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
        return http.request.env['ir.ui.view']._render_template("ev_helpdesk.ticket_submit_form", vals)

    @http.route('/my/help_custom/rating_page/<int:question_related_id>', type='json', auth="user", website=True)
    def rating_page(self, question_related_id=None):
        return http.request.env['ir.ui.view']._render_template("ev_helpdesk.questions_rating", {'question_related_id': question_related_id})

    @http.route([
        '/my/help_custom/<int:question_id>',
        '/my/help_custom/<int:question_id>/<access_token>'
    ], type='json', auth="user", website=True)
    def get_helpdesk_custom(self, question_id=None, access_token=None, **kw):
        try:
            if not question_id:
                root_question = self.get_root_question()
                if not root_question:
                    raise UserError(_("There is no root question appropriate with you! Contact with your manager to support"))
                question_sudo = self._document_check_access('question.question', root_question, access_token)
            else:
                question_sudo = self._document_check_access('question.question', question_id, access_token)

        except (AccessError, MissingError):
            return request.redirect('#')
        question_vals = self._question_get_page_view_values(question_sudo, access_token, **kw)
        question_vals.update({'is_question_root': True if question_sudo.is_question_root else False})
        return http.request.env['ir.ui.view']._render_template("ev_helpdesk.questions_followup", question_vals)

    @http.route([
        '/my/helpdesk/<int:question_id>',
        '/my/helpdesk/<int:question_id>/<access_token>'
    ], type='http', auth="user", website=True)
    def get_helpdesk(self, question_id=None, access_token=None, **kw):
        try:
            if not question_id:
                root_question = self.get_root_question()
                if not root_question:
                    raise UserError(_("There is no root question appropriate with you! Contact with your manager to support"))
                question_sudo = self._document_check_access('question.question', root_question, access_token)
            else:
                question_sudo = self._document_check_access('question.question', question_id, access_token)

        except (AccessError, MissingError):
            return request.redirect('#')
        question_vals = self._question_get_page_view_values(question_sudo, access_token, **kw)
        question_vals.update({'is_question_root': True if question_sudo.is_question_root else False})
        return request.render('ev_helpdesk.questions_main_page', question_vals)


    def get_root_question(self):
        """
        get root question based on helpdesk department applied
        """
        root_question = self.env['question.question'].search(
            [('is_question_root', '=', True), ('department_request_ids', 'in', self.env.uid)], limit=1)
        return root_question or False

    def _question_get_page_view_values(self, question, access_token, **kwargs):
        values = {
            'id': question.id,
            'name': question.name,
            'answer_detail': question.answer_detail,
            'answers': question.answer_ids,
            'page_name': 'question',
            'default_url': '/my/question/' + str(question.id),
        }
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, filterby='all', search=None,
                            groupby='none', search_in='content', **kw):
        values = self._prepare_portal_layout_values()


        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'stage_id'},
            'reference': {'label': _('Reference'), 'order': 'id'},
            'update': {'label': _('Last Stage Update'), 'order': 'date_last_stage_update desc'},
        }
        searchbar_filters = {
            'open': {'label': _('Open'), 'domain': [('create_uid', '=', request.env.uid), ('stage_id.is_close', '=', False)]},
            'assigned': {'label': _('Assigned'), 'domain': [('create_uid', '=', request.env.uid),('user_id', '!=', False)]},
            'unassigned': {'label': _('Unassigned'), 'domain': [('create_uid', '=', request.env.uid),('user_id', '=', False)]},
            'closed': {'label': _('Closed'), 'domain': [('create_uid', '=', request.env.uid),('stage_id.is_close', '!=', False)]},
            'all': {'label': _('All'), 'domain': [('create_uid', '=', request.env.uid)]},
            # 'last_message_sup': {'label': _('Last message is from support')},
            # 'last_message_cust': {'label': _('Last message is from customer')},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': Markup(_('Search <span class="nolabel"> (in Content)</span>'))},
            # 'message': {'input': 'message', 'label': _('Search in Messages')},
            # 'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'id': {'input': 'id', 'label': _('Search in Reference')},
            'status': {'input': 'status', 'label': _('Search in Stage')},
            'department': {'input': 'department', 'label': _('Search in Department')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'stage': {'input': 'stage_id', 'label': _('Stage')},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        domain = searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            # if search_in in ('customer', 'all'):
            #     search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            # if search_in in ('message', 'all'):
            #     discussion_subtype_id = request.env.ref('mail.mt_comment').id
            #     search_domain = OR([search_domain, [('message_ids.body', 'ilike', search),
            #                                         ('message_ids.subtype_id', '=', discussion_subtype_id)]])
            if search_in in ('status', 'all'):
                search_domain = OR([search_domain, [('stage_id', 'ilike', search)]])
            if search_in in ('department', 'all'):
                search_domain = OR([search_domain, [('helpdesk_department_id', 'ilike', search)]])
            domain += search_domain

        # pager
        tickets_count = request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'search_in': search_in,
                      'search': search, 'groupby': groupby, 'filterby': filterby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        tickets = request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page,
                                                        offset=pager['offset'])
        request.session['my_tickets_history'] = tickets.ids[:100]

        if groupby == 'stage':
            grouped_tickets = [request.env['helpdesk.ticket'].concat(*g) for k, g in
                               groupbyelem(tickets, itemgetter('stage_id'))]
        else:
            grouped_tickets = [tickets]

        values.update({
            'date': date_begin,
            'grouped_tickets': grouped_tickets,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'search_in': search_in,
            'search': search,
            'filterby': filterby,
        })
        return request.render("helpdesk.portal_helpdesk_ticket", values)
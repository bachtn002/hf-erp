# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response


def create_helpdesk_log_api(data, message):
    vals = {
        'data': data,
        'message': message,
    }
    request.env['helpdesk.ticket.log'].sudo().create(vals)
    return

class HelpdeskTicketController(http.Controller):

    @http.route('/helpdesk_ticket/create', methods=['POST'], type='json', auth='public')
    def create_ticket(self, **kwargs):
        params = request.jsonrequest
        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            create_helpdesk_log_api(params, mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id or api_id.code != '/helpdesk_ticket/create':
            mesg = _("Token connection code no matching!")
            create_helpdesk_log_api(params, mesg)
            return Response.error(mesg, data={}, code='401').to_json()

        if 'helpdesk_department' not in params:
            mesg = _("Missing params helpdesk department!")
            create_helpdesk_log_api(params, mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if params.get('name') == '':
            mesg = _("Invalid params name!")
            create_helpdesk_log_api(params, mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        helpdesk_department = request.env['helpdesk.department'].sudo().search(
            [('name', '=ilike', params.get('helpdesk_department').strip())], limit=1)
        if not helpdesk_department:
            mesg = _("Invalid params helpdesk department!")
            create_helpdesk_log_api(params, mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        try:
            #phân công cho, check có thuộc bộ phận
            user_id = False
            if 'user_email' in params:
                if params['user_email'] != '':
                    user_id = request.env['res.users'].sudo().search(
                        [('login', '=', params.get('user_email').strip())], limit=1)
                    if not user_id:
                        mesg = _("User not in system")
                        raise Exception(mesg)
                    if user_id.id not in helpdesk_department.user_ids.ids:
                        mesg = _('User not in helpdesk department')
                        raise Exception(mesg)

            ticket_type = request.env['helpdesk.ticket.type'].sudo().search(
                [('name', '=ilike', params.get('ticket_type').strip())], limit=1)
            if not ticket_type or (helpdesk_department.id not in ticket_type.x_helpdesk_department_id.ids):
                mesg = _("Ticket type not invalid")
                raise Exception(mesg)

            tags = request.env['helpdesk.tag'].sudo().search([('name', '=ilike', params.get('tags').strip())], limit=1)
            partner_id = request.env['res.partner'].sudo().search([('phone', '=', params.get('partner_phone').strip())],
                                                                  limit=1)
            if not partner_id and 'partner_email' in params:
                if params.get('partner_email').strip() != '':
                    partner_id = request.env['res.partner'].sudo().search(
                        [('email', '=', params.get('partner_email').strip())], limit=1)
            shop_id = request.env['pos.shop'].sudo().search([('code', '=ilike', params.get('pos_shop_code').strip())], limit=1)
            vals = {
                'name': params.get('name'),
                'user_id': user_id.id if user_id else False,
                'ticket_type_id': ticket_type.id,
                'priority': str(params.get('priority')),
                'tag_ids': [(6, 0, [tags.id])] if tags else None,
                'partner_id': partner_id.id if partner_id else False,
                'helpdesk_department_id': helpdesk_department.id,
                'x_phone': partner_id.phone if partner_id else False,
                'partner_name': partner_id.name if partner_id else False,
                'partner_email': partner_id.email if partner_id else False,
                'description': params.get('description'),
                'x_note': params.get('note'),
                'x_shop_id': shop_id.id if shop_id else False,
                'x_ref': params.get('x_ref'),
            }
            request.env['helpdesk.ticket'].sudo().create(vals)
            # helpdesk_ticket.sudo().send_message_email_team()
            mesg = _('Create helpdesk ticket successfully!')
            create_helpdesk_log_api(params, mesg)
            return Response.success(mesg, data={}).to_json()

        except Exception as e:
            create_helpdesk_log_api(params, str(e))
            return Response.error(str(e), data={}, code='400').to_json()

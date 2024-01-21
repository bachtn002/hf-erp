import base64

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper


class TicketController(http.Controller):

    @http.route('/helpdesk/home/', type='http', auth='user', website=True)
    def helphome(self, **kw):
        link_drive = request.env['ir.config_parameter'].sudo().get_param('ev_helpdesk.link_drive')
        vals = {
            'link_drive': link_drive if link_drive else '#'
        }
        return request.render('ev_helpdesk.home_ticket_portal', vals)

    def _portal_post_filter_params(self):
        return ['token', 'hash', 'pid']


    @http.route('/help/tickets/send_ticket', methods=['POST'], type='http', auth='user', website=True)
    def send_ticket(self, **kw):
        params = request.params
        helpdesk_department_id = request.env['helpdesk.department'].sudo().search([('name', '=', params.get('helpdesk_department'))], limit=1)
        app = request.env['app.support'].sudo().search([('name', '=', params.get('app'))])
        ticket_type = request.env['helpdesk.ticket.type'].sudo().search([('name', '=', params.get('ticket_type'))])
        user_id = request.env.user
        vals = {
            'name': params.get('name'),
            # 'team_id': team.id if team else False,
            'helpdesk_department_id': helpdesk_department_id.id or False,
            'ticket_type_id': ticket_type.id if ticket_type else False,
            'partner_id': user_id.partner_id.id if user_id else False,
            'x_app_sp_id': app.id if app else False,
            'x_phone': params.get('phone'),
            'partner_email': params.get('email'),
            'x_id_sp': params.get('id_app'),
            'x_pass_sp': params.get('pass_app'),
            'description': params.get('description'),
            'x_pos_shop_code': params.get('pos_shop_code'),
        }
        new_ticket_created = request.env['helpdesk.ticket'].sudo().create(vals)
        request.env.cr.commit()

        if params.get('attachment', False):
            Attachments = request.env['ir.attachment']
            name = params.get('attachment').filename
            file = params.get('attachment')
            attachment = file.read()
            attachment_ticket = Attachments.sudo().create({
                'name': name,
                'res_name': name,
                'type': 'binary',
                'res_model': 'helpdesk.ticket',
                'res_id': new_ticket_created.id,
                'datas': base64.encodebytes(attachment),
            })

            # Post a message in chatbox with attachment created
            post_values = {
                'res_model': 'helpdesk.ticket',
                'res_id': new_ticket_created.id,
                'message': "",
                'send_after_commit': False,
                'attachment_ids': False,  # will be added afterward
            }
            post_values.update((fname, kw.get(fname)) for fname in self._portal_post_filter_params())
            message = _message_post_helper(**post_values)

            # sudo write the attachment to bypass the read access
            # verification in mail message
            record = request.env['helpdesk.ticket'].browse(new_ticket_created.id)
            message_values = {'res_id': new_ticket_created.id, 'model': 'helpdesk.ticket'}
            attachments = record._message_post_process_attachments([], [attachment_ticket.id], message_values)

            if attachments.get('attachment_ids'):
                message.sudo().write(attachments)
        return request.redirect('/my/tickets')


    @http.route('/help/tickets/send_rating', methods=['GET'], type='http', auth='user', website=True)
    def send_rating(self):
        params = request.params
        team = request.env['helpdesk.team'].sudo().search([('name', '=', params.get('team'))])
        app = request.env['app.support'].sudo().search([('name', '=', params.get('app'))])
        ticket_type = request.env['helpdesk.ticket.type'].sudo().search([('name', '=', params.get('ticket_type'))])
        user_id = request.env.user
        vals = {
            'name': params.get('name'),
            'team_id': team.id if team else False,
            'ticket_type_id': ticket_type.id if ticket_type else False,
            'partner_id': user_id.partner_id.id if user_id else False,
            'x_app_sp_id': app.id if app else False,
            'x_phone': params.get('phone'),
            'x_id_sp': params.get('id_app'),
            'x_pass_sp': params.get('pass_app'),
            'description': params.get('description'),
        }
        request.env['helpdesk.ticket'].sudo().create(vals)
        request.env.cr.commit()
        return request.redirect('/my/tickets')

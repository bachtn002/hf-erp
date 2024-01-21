# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HelpdeskTicketTemplate(models.Model):
    _name = 'helpdesk.ticket.template'
    _description = "Helpdesk ticket template"
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char('Name')
    user_ids = fields.Many2many('res.users', string="Users")
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Ticket type")
    description = fields.Text('Description')
    state = fields.Selection([('draft', 'Draft'), ('assigned', 'Assigned'), ('cancel', 'Cancel')], string="State",
                             default="draft")
    ref_helpdesk_ticket = fields.Many2many('helpdesk.ticket', string="Helpdesk ticket")
    solution_detail = fields.Html(string="Solution detail", default="")
    tag_ids = fields.Many2many('helpdesk.tag', string='Tags')
    helpdesk_department_id = fields.Many2one('helpdesk.department', string="Helpdesk Department")
    domain_user_ids = fields.Many2many('res.users', compute='_compute_domain_user_ids')

    @api.depends('helpdesk_department_id')
    def _compute_domain_user_ids(self):
        for record in self:
            helpdesk_users = self.env['res.users'].search(
                [('x_helpdesk_department_id', '=', record.helpdesk_department_id.id)]).ids
            record.domain_user_ids = [(6, 0, helpdesk_users)]

    @api.onchange('helpdesk_department_id')
    def onchange_helpdesk_department_id(self):
        if self.helpdesk_department_id:
            self.user_ids = False
            self.ticket_type_id = False

    def button_assign(self):
        if self.state == 'draft':
            for user_id in self.user_ids:
                team_default_id = self.env['helpdesk.team'].search([('member_ids', 'in', self.env.uid)], limit=1).id
                if not team_default_id:
                    team_default_id = self.env['helpdesk.team'].search([], limit=1).id
                stage = self.env['helpdesk.stage'].search(
                    [('is_start', '=', True), ('team_ids', 'in', team_default_id)], limit=1)
                helpdesk_ticket = self.env['helpdesk.ticket'].create({
                    'name': self.name,
                    'ticket_type_id': self.ticket_type_id.id,
                    'description': self.description,
                    'user_id': user_id.id,
                    'helpdesk_department_id': self.helpdesk_department_id.id,
                    'partner_id': self.env.user.partner_id.id,
                    'x_solution_detail': self.solution_detail,
                    'tag_ids': [(6, 0, self.tag_ids.ids)],
                    'stage_id': stage.id,
                })

                stage = self.env['helpdesk.stage'].search(
                    [('name', '=', 'Tiếp nhận'), ('team_ids', '=', team_default_id)], limit=1)
                if not stage:
                    stage = self.env['helpdesk.stage'].search(
                        [('x_is_receive', '=', True), ('team_ids', '=', team_default_id)], limit=1)
                helpdesk_ticket.write({'stage_id': stage.id})

                template = helpdesk_ticket.stage_id.template_id
                if template:
                    template.send_mail(helpdesk_ticket.id, force_send=False)

                self.ref_helpdesk_ticket = [(4, helpdesk_ticket.id)]
            self.write({'state': 'assigned'})
        else:
            raise UserError(_('You only sent at state draft!'))

    def button_cancel(self):
        if self.state == 'draft':
            self.write({'state': 'cancel'})
        else:
            raise UserError(_('You only sent at state draft!'))

    def button_back_to_draft(self):
        if self.state == 'cancel':
            self.write({'state': 'draft'})
        else:
            raise UserError(_('You only sent at state cancel!'))

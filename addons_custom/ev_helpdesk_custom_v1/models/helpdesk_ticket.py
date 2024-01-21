# -*- coding: utf-8 -*-
from odoo import models, api, _
from dateutil import relativedelta
from datetime import datetime
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def create_ticket_rating(self, rating_value, feedback):
        model_id = self.env['ir.model']._get('helpdesk.ticket').id
        self.env['rating.rating'].create({
            'res_model_id': model_id,
            'res_id': self.id,
            'partner_id': self.env.user.partner_id.id,
            'rating': rating_value,
            'feedback': feedback,
        })
        rating = ''
        if rating_value == 1:
            rating = _('Highly Dissatisfied')
        elif rating_value == 2:
            rating = _('Dissatisfied')
        elif rating_value == 3:
            rating = _('Not Satisfied')
        elif rating_value == 4:
            rating = _('Satisfied')
        elif rating_value == 5:
            rating = _('Highly Satisfied')
        for item in self:
            item.message_post_with_view('ev_helpdesk_custom_v1.log_rating_template',
                                        values={'rating': str(rating_value) + ' - ' + rating,
                                                'feedback': feedback},
                                        message_type='comment')

    @api.depends('team_id', 'helpdesk_department_id')
    def _compute_domain_user_ids(self):
        for task in self:
            if task.team_id and task.team_id.visibility_member_ids:
                helpdesk_manager = self.env['res.users'].search(
                    [('groups_id', 'in', self.env.ref('helpdesk.group_helpdesk_manager').id)])
                task.domain_user_ids = [
                    (6, 0, (helpdesk_manager + task.team_id.visibility_member_ids).ids)]
                # add domain based on helpdesk department
                task.domain_user_ids = [(6, 0, task.helpdesk_department_id.user_ids.ids)]
            else:
                helpdesk_users = self.env['res.users'].search(
                    [('groups_id', 'in', self.env.ref('helpdesk.group_helpdesk_user').id)]).ids
                task.domain_user_ids = [(6, 0, helpdesk_users)]
                # add domain based on helpdesk department
                task.domain_user_ids = [(6, 0, task.helpdesk_department_id.user_ids.ids)]

    def write(self, vals):
        if 'stage_id' in vals:
            # Update close_date
            stage_change = self.env['helpdesk.stage'].browse(vals.get('stage_id'))
            if stage_change.is_close:
                vals.update({'close_date': datetime.now()})
            for record in self:
                # Ticket can be reopen when them in stage close
                if record.stage_id.is_close:
                    # Max days allow to reopen
                    max_day = self.env['ir.config_parameter'].sudo().get_param('ev_helpdesk.days_allow_back_to_new_ticket')
                    if record.close_date:
                        if record.close_date + relativedelta.relativedelta(days=int(max_day)) <= datetime.now():
                            raise UserError(_("Cannot open ticket after period %s days") % max_day)
                    # Check Stage allow to reopen ticket
                    stage_config = self.env['helpdesk.stage'].sudo().search(
                        [('team_ids', 'in', (record.team_id.id)), ('is_close', '=', False),
                         ('is_stage_back', '=', True)], limit=1)
                    if vals['stage_id'] != stage_config.id:
                        raise UserError(_("Only Stage %s can be reopen ticket") % (stage_config.name))

        return super(HelpdeskTicket, self).write(vals)

    def _compute_is_self_assigned(self):
        for ticket in self:
            # Only can assign ticket to user when ticket on New stage
            if not self.stage_id.is_start:
                ticket.is_self_assigned = True
            else:
                ticket.is_self_assigned = False

    def action_set_to_draft(self):
        for record in self:
            stage_config = self.env['helpdesk.stage'].sudo().search(
                [('team_ids', 'in', (record.team_id.id)), ('is_close', '=', False),
                 ('is_stage_back', '=', True)], limit=1)
            if stage_config:
                stage_id = stage_config.id
            else:
                stage_id = record.team_id._determine_stage()[record.team_id.id].id,
            record.stage_id = stage_id
            record.user_id = False

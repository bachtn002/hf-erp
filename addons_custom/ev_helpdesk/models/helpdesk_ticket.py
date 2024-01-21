from odoo import models, fields, api, _, SUPERUSER_ID

from odoo.addons.helpdesk.models.helpdesk_ticket import HelpdeskTicket as HelpdeskTickitEnterprise

from odoo.exceptions import ValidationError, UserError


def _notify_get_groups(self, msg_vals=''):
    """ Handle helpdesk users and managers recipients that can assign
    tickets directly from notification emails. Also give access button
    to portal and portal customers. If they are notified they should
    probably have access to the document. """
    groups = super(HelpdeskTickitEnterprise, self)._notify_get_groups(msg_vals)

    self.ensure_one()
    for group_name, group_method, group_data in groups:
        if group_name != 'customer':
            group_data['has_button_access'] = True

    if self.user_id:
        return groups

    take_action = self._notify_get_action_link('assign')
    helpdesk_actions = [{'url': take_action, 'title': _('Assign to me')}]
    helpdesk_user_group_id = self.env.ref('helpdesk.group_helpdesk_user').id
    new_groups = [(
        'group_helpdesk_user',
        lambda pdata: pdata['type'] == 'user' and helpdesk_user_group_id in pdata['groups'],
        {'actions': helpdesk_actions}
    )]
    return new_groups + groups

HelpdeskTickitEnterprise._notify_get_groups = _notify_get_groups.__get__(None, HelpdeskTickitEnterprise)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_phone = fields.Char('Phone Number')
    x_app_sp_id = fields.Many2one('app.support', 'App Support')
    x_id_sp = fields.Char('Id Support')
    x_pass_sp = fields.Char('Pass Support')
    x_problem_solution = fields.Text('Problem Solution')
    # x_partner_email = fields.Char('Email')
    x_is_rating = fields.Boolean("Is get ticket rating?")
    x_allow_set_back_draft = fields.Boolean("Is allow set back to draft?")

    # Bo phan ho tro
    helpdesk_department_id = fields.Many2one('helpdesk.department', string="Helpdesk Department")

    # Ma cua hang
    x_pos_shop_code = fields.Char("Pos shop code")

    def action_set_to_cancel(self):
        for re in self:
            stage_cancel = self.env['helpdesk.stage'].search([('is_cancel', '=', True), ('team_ids', 'in', self.team_id.ids)], limit=1)
            if not stage_cancel:
                raise UserError(_("There is no closing stage available, Please connect with your manager!"))
            re.stage_id = stage_cancel.id

    def action_set_to_draft(self):
        for record in self:
            stage_config = self.env['ir.config_parameter'].sudo().get_param('ev_helpdesk.stage_allow_user_back_ticket')
            stage_obj = self.env['helpdesk.stage'].browse(int(stage_config))
            if stage_obj:
                stage_id = stage_obj.id
            else:
                stage_id = record.team_id._determine_stage()[record.team_id.id].id,
            record.stage_id = stage_id
            record.user_id = False

    def create_ticket_rating(self, rating_value, feedback):
        model_id = self.env['ir.model']._get('helpdesk.ticket').id
        created_rating = self.env['rating.rating'].search([('res_model_id', '=', model_id), ('res_id', '=', self.id),
                                                           ('partner_id', '=', self.env.user.partner_id.id)])
        if not created_rating:
            self.x_is_rating = True
            self.env['rating.rating'].create({
                'res_model_id': model_id,
                'res_id': self.id,
                'partner_id': self.env.user.partner_id.id,
                'rating': rating_value,
                'feedback': feedback,
            })

    def _notify_get_groups(self, msg_vals=None):
        """ Handle helpdesk users and managers recipients that can assign
        tickets directly from notification emails. Also give access button
        to portal and portal customers. If they are notified they should
        probably have access to the document. """
        groups = super(HelpdeskTicket, self)._notify_get_groups(msg_vals=msg_vals)

        self.ensure_one()
        for group_name, group_method, group_data in groups:
            if group_name != 'customer':
                group_data['has_button_access'] = True

        if self.user_id:
            return groups

        take_action = self._notify_get_action_link('assign')
        helpdesk_actions = [{'url': take_action, 'title': _('Assign to me')}]
        helpdesk_user_group_id = self.env.ref('helpdesk.group_helpdesk_user').id
        new_groups = [(
            'group_helpdesk_user',
            lambda pdata: pdata['type'] == 'user' and helpdesk_user_group_id in pdata['groups'],
            {'actions': helpdesk_actions}
        )]
        return new_groups + groups

    @api.model
    def create(self, vals):
        try:
            res = super(HelpdeskTicket, self).create(vals)
            res.send_message_email_team()
            return res
        except Exception as e:
            raise ValidationError(e)

    def send_message_email_team(self):
        try:
            template = self.stage_id.template_id
            if template:
                template.send_mail(self.id, force_send=True)
        except Exception as e:
            raise ValidationError(e)

    # Menu Ticket của tôi: Lọc ticket của user login tạo + User thuộc phòng ban của user login tạo
    def ticket_department_created_filter_act(self):
        return {
            'name': _("My Department Tickets Members"),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'view_type': 'form',
            'views': [[False, 'tree'], [False, 'form'], [False, 'kanban']],
            'domain': ['|', ('create_uid', '=', self.env.uid),
                       ('create_uid', 'in', self.env.user.x_helpdesk_department_id.user_ids.ids)],
            'context': {'search_default_is_open': 1},
            'target': 'current',
        }

    # Menu Xử lý ticket: Lọc ticket được giao cho phòng ban hiện tại
    def ticket_department_assigned_filter_act(self):
        return {
            'name': _("My Department Tickets Assigned"),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'view_type': 'form',
            'views': [[False, 'tree'], [False, 'form'],  [False, 'kanban']],
            'domain': ['|', '|',  ('user_id', '=', self.env.uid),
                       ('user_id', 'in', self.env.user.x_helpdesk_department_id.user_ids.ids),
                       '&', ('user_id', '=', False),('helpdesk_department_id', '=', self.env.user.x_helpdesk_department_id.id)],
            'context': {'search_default_is_open': 1},
            'target': 'current',
        }

    def assign_ticket_to_self(self):
        """
        - Get all stage of user's team
        - change stage from new => progress (based on sequence)
        """
        self.ensure_one()
        self.user_id = self.env.user
        stages = self.env['helpdesk.stage'].search_read([('team_ids', 'in', self.team_id.ids)], ['id', 'sequence'], order='sequence')
        for i, stage in enumerate(stages):
            if stage['id'] == self.stage_id.id and not (i+1 == len(stages)):
                self.stage_id = self.env['helpdesk.stage'].browse(stages[i+1]['id']).id
                break
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_solution_detail = fields.Html(string="Solution detail", default="")
    x_shop_id = fields.Many2one('pos.shop', string="Pos shop")
    x_ref = fields.Char('Reference No')
    helpdesk_department_id = fields.Many2one('helpdesk.department', ondelete='restrict')

    # Menu Tất cả ticket: lọc danh sách ticket thuộc bộ phận được phép theo thông tin user đăng nhập
    def ticket_department_all_filter_act(self):
        # res_users = self.env.user.x_helpdesk_department_id.user_ids | self.env.user.x_helpdesk_department_ids.mapped(
        #     'user_ids')
        helpdesk_department = self.env.user.x_helpdesk_department_id | self.env.user.x_helpdesk_department_ids
        return {
            'name': _("My All Tickets"),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'view_type': 'form',
            'views': [[False, 'tree'], [False, 'form'], [False, 'kanban']],
            'domain': [('helpdesk_department_id', 'in', helpdesk_department.ids)],
            'context': {'search_default_is_open': 1},
            'target': 'current',
        }

        # Menu Xử lý ticket: Lọc ticket được giao cho phòng ban hiện tại
        # Thêm check Chỉ được xử lý ticket của tôi

    def ticket_department_assigned_filter_act(self):
        if self.env.user.x_is_allow_helpdesk_department:
            domain = [('user_id', '=', self.env.uid)]
        else:
            helpdesk_department = self.env.user.x_helpdesk_department_id
            res_users = helpdesk_department.mapped('user_ids')
            domain = ['|', '|', ('user_id', '=', self.env.uid),
                      ('user_id', 'in', res_users.ids),
                      '&', ('user_id', '=', False),
                      ('helpdesk_department_id', 'in', helpdesk_department.ids)]

        return {
            'name': _("My Department Tickets Assigned"),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'view_type': 'form',
            'views': [[False, 'tree'], [False, 'form'], [False, 'kanban']],
            'domain': domain,
            'context': {'search_default_is_open': 1},
            'target': 'current',
        }

    # Menu Ticket của tôi:
    # TH tích chọn chỉ xem ticket của tôi Lọc ticket của user login tạo
    # TH khác :Lọc ticket của user login tạo + User thuộc phòng ban của user login tạo
    def ticket_department_created_filter_act(self):
        if self.env.user.x_is_allow_helpdesk_department:
            domain = [('create_uid', '=', self.env.uid)]
        else:
            helpdesk_department = self.env.user.x_helpdesk_department_id
            domain = ['|', ('create_uid', '=', self.env.uid),
                       ('create_uid', 'in', helpdesk_department.user_ids.ids)]
        return {
            'name': _("My Department Tickets Members"),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'view_type': 'form',
            'views': [[False, 'tree'], [False, 'form'], [False, 'kanban']],
            'domain': domain,
            'context': {'search_default_is_open': 1},
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        # Bắt buộc nhập phương hướng giải quyết khi ở trạng thái hoàn thành
        if 'stage_id' in vals:
            stage = self.env['helpdesk.stage'].search([('id', '=', vals['stage_id'])])
            if stage.name == 'Hoàn thành' or stage.x_is_done:
                if not self.x_problem_solution:
                    raise UserError(_('Problem Solution is required!'))
            if stage.name in ('Tiếp nhận', 'Hoàn thành') or stage.is_cancel or stage.x_is_done or stage.x_is_receive:
                if not self.user_id:
                    raise UserError(_('User is required!'))

        if 'x_pos_shop_code' in vals:
            if vals['x_pos_shop_code'] != '':
                x_shop_id = self.env['pos.shop'].search([('code', '=', vals['x_pos_shop_code'])], limit=1).id
                vals['x_shop_id'] = x_shop_id
        return super(HelpdeskTicket, self).create(vals)

    def write(self, vals):
        # Bắt buộc nhập phương hướng giải quyết khi ở trạng thái hoàn thành
        if 'stage_id' in vals:
            stage = self.env['helpdesk.stage'].search([('id', '=', vals['stage_id'])])
            for record in self:
                if stage.name == 'Hoàn thành' or stage.x_is_done:
                    if not record.x_problem_solution:
                        raise UserError(_('Problem Solution is required!'))
                # Bắt buộc nhập người xử lý ticket khi ở trạng thái tiếp nhận, hủy, hoàn thành
                if stage.name in (
                'Tiếp nhận', 'Hoàn thành') or stage.is_cancel or stage.x_is_done or stage.x_is_receive:
                    if not record.user_id:
                        raise UserError(_('User is required!'))

        return super(HelpdeskTicket, self).write(vals)

    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.sudo().read()[0]
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        return action

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError


class ResPartnerPermission(models.Model):
    _inherit = 'res.partner'

    
    def write(self, vals):
        access_edit_partner = False
        if 'is_company' in vals:
            access_edit_partner = True
        if 'phone' in vals:
            access_edit_partner = False
        if 'name' in vals:
            access_edit_partner = False
        if 'loyalty_points' in vals:
            access_edit_partner = True
        if 'signup_token' in vals:
            access_edit_partner = True
        if 'tz' in vals:
            access_edit_partner = True
        if self.env.user.has_group('ev_permission_edit_partner.group_edit_partner'):
            access_edit_partner = True
        if access_edit_partner:
            return super(ResPartnerPermission, self).write(vals)
        else:
            raise AccessError('Rất tiếc bạn không có quyền thay đổi thông tin đối tác. Xin hãy liên hệ với quản trị viên')

    def unlink(self):
        if not self.env.user.has_group('ev_permission_edit_partner.group_edit_partner'):
            raise AccessError(
                'Rất tiếc bạn không có quyền thay đổi thông tin đối tác. Xin hãy liên hệ với quản trị viên')
        return super(ResPartnerPermission, self).unlink()
            


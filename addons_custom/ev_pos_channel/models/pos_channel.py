# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosChannel(models.Model):
    _name = 'pos.channel'
    _description = 'Pos Channel'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', track_visibility='always')
    code = fields.Char(string='Code', track_visibility='always', index=True)
    is_allow_pos = fields.Boolean(string='Allow Select In Pos', default=True)
    is_allow_send_zns = fields.Boolean(string='Allow Send ZNS', default=False)
    is_default_pos = fields.Boolean(string='Default In Pos', default=False)
    is_online_channel = fields.Boolean(string='Is Online Channel', default=False)
    active = fields.Boolean(string='Active', default=True)
    pos_payment_methods_ids = fields.Many2many(comodel_name='pos.payment.method',
                                           relation='pos_channel_pos_payment_method_rel',
                                           column1='pos_channel_id', column2='pos_payment_method_id',
                                           string='Payment Method')
    is_not_allow_editing = fields.Boolean(string='Is Allow Editing When Syncing', default=False, tracking="1")

    @api.constrains('code')
    def _check_unique_code(self):
        for item in self:
            if self.search_count([('code', '=', item.code)]) > 1:
                raise UserError(_('Pos channel code must be unique.'))

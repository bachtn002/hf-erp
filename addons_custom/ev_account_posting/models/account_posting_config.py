# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, pycompat

import logging

_logger = logging.getLogger(__name__)


class AccountPostingConfig(models.Model):
    _name = 'account.posting.config'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Code", default="/")
    account_from = fields.Many2one('account.account', string="Account From", required=True, copy=False)
    account_to = fields.Many2one('account.account', string="Account To", required=True, copy=False)
    active = fields.Boolean(string="Active", default=True)
    type = fields.Selection([('debit','Debit'), ('credit', 'Credit'),('balance','Balance')], 'Type', default='balance', required=True)
    description = fields.Char('Description')
    sequence = fields.Integer('Sequence')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    _sql_constrains = [
        ("code_unique",
         "UNIQUE(code)",
         "Duplicated code in account forward"),
    ]

    @api.model
    def create(self, vals_list):
        account_from = self.env['account.account'].search([('id','=', vals_list['account_from'])])
        account_to = self.env['account.account'].search([('id', '=', vals_list['account_to'])])
        vals_list['name'] = account_from.code + '-' + account_to.code
        return super(AccountPostingConfig, self).create(vals_list)

    def write(self, vals):
        res = super(AccountPostingConfig, self).write(vals)
        if 'account_from' in vals or 'account_to' in vals:
            self.update({'name': self.account_from.code + '-' + self.account_to.code})
        return res


        
            




# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    x_swift_bank = fields.Char(string="Swift")
    x_branch_bank = fields.Char(string="Branch")
    x_active = fields.Boolean(string="Active", related='bank_id.active')

    def name_get(self):
        res = []
        for item in self:
            if item.bank_id.name != False:
                name = item.bank_id.name + " " + (item.x_branch_bank or "") + "(" + item.acc_number + ")"
            else:
                name = item.acc_number
            res.append((item.id, name))
        return res


class ResPartner(models.Model):
    _inherit = 'res.partner'

    bank_ids = fields.One2many('res.partner.bank', 'partner_id', string='Banks', domain=[('x_active', '=', True)])
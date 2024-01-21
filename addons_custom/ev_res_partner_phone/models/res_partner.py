# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('phone')
    def check_unique_phone(self):
        for record in self:
            res_partner = self.env['res.partner'].search([('phone', '=', record.phone), ('id', '!=', record.id)])
            if res_partner:
                raise ValidationError(_('Phone number already exists.'))

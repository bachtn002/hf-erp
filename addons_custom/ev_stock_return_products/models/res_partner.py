# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_points = fields.Float(company_dependent=True,
                                  help='The loyalty points the user won as part of a Loyalty Program')
    x_is_supplier = fields.Boolean(string='Is supplier', default=False)

    _sql_constraints = [
        ('ref_uniq', 'unique (ref)', 'The ref must be unique!')
    ]

    def name_get(self):
        res = []
        for partner in self:
            name = partner._get_name()
            if partner.ref:
                name = '[' + partner.ref + '] ' + partner._get_name()
            res.append((partner.id, name))
        return res

    @api.model
    def create(self, vals):
        try:
            check_company_type = False
            check_vat = False
            try:
                if vals['company_type']:
                    check_company_type = True
            except:
                check_company_type = False
            try:
                if vals['vat']:
                    check_vat = True
            except:
                check_vat = False

            if check_company_type == False or check_vat == False:
                return super(ResPartner, self).create(vals)
            type = ''
            if check_company_type:
                type = vals['company_type']
            vat = ''
            if check_vat:
                vat = vals['vat']
            if type == 'company':
                # if self.vat != vals['vat']:
                res_partner = self.env['res.partner'].search(
                    [('vat', '=', vat), ('company_type', '=', 'company'), ('active', '=', True)])
                if not res_partner:
                    return super(ResPartner, self).create(vals)
                else:
                    raise UserError(_('VAT already exists on the system!'))
            else:
                return super(ResPartner, self).create(vals)
        except Exception as e:
            raise ValidationError(e)

    def write(self, vals):
        try:
            check_company_type = False
            check_vat = False
            try:
                if vals['company_type']:
                    check_company_type = True
            except:
                check_company_type = False
            try:
                if vals['vat']:
                    check_vat = True
            except:
                check_vat = False
            type = ''
            if check_company_type == False and check_vat == False:
                return super(ResPartner, self).write(vals)
            if check_company_type:
                type = vals['company_type']
            else:
                type = self.company_type
            vat = ''
            if check_vat:
                vat = vals['vat']
            else:
                vat = self.vat
            if type == 'company':
                res_partner = self.env['res.partner'].search(
                    [('vat', '=', vat), ('company_type', '=', 'company'), ('active', '=', True)])
                if not res_partner:
                    return super(ResPartner, self).write(vals)
                elif self.id in res_partner.ids and len(res_partner) == 1:
                    return super(ResPartner, self).write(vals)
                else:
                    raise UserError(_('VAT already exists on the system!'))
            else:
                return super(ResPartner, self).write(vals)
        except Exception as e:
            raise ValidationError(e)

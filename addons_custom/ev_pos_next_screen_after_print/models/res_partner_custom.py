import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError


class PartnerCustom(models.Model):
    _inherit = 'res.partner'
    date_of_birth = fields.Date(string=_("Date of birth"))

    @api.constrains('phone', 'company_type')
    def _check_release_date(self):
        for record in self:
            if record.company_type == 'person':
                if record.phone:
                    query = """
                                SELECT id
                                FROM res_partner WHERE active = true and phone = '%s'
                            """ % (record.phone)
                    self._cr.execute(query)
                    res_record = self._cr.dictfetchall()
                    # res_record = self.env['res.partner'].search([('phone', '=', record.phone)])
                    if len(res_record) > 1:
                        raise UserError(_('Phone number is existed'))
                    elif len(record.phone) > 15:
                        raise UserError(_('Length phone must less than 15'))
                    elif record.phone.isdigit() is False:
                        raise UserError(_('Phone Number must have not character'))
                else:
                    raise UserError(_('Phone number is not input'))

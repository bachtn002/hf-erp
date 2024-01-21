# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_groups = fields.Many2many(comodel_name='res.partner.group',
                                      relation='res_partner_res_partner_group_rel',
                                      string=_('Partner groups'))

    # nâng cấp bị lỗi view nên thêm vào
    loyalty_points = fields.Float(company_dependent=True,
                                  help='The loyalty points the user won as part of a Loyalty Program')


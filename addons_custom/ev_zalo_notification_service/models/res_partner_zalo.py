# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartnerZalo(models.Model):
    _name = 'res.partner.zalo'
    _description = 'Partner Map Zalo'

    phone = fields.Char('Phone')
    zalo_id = fields.Char('Zalo ID')

    _sql_constraints = [('zalo_id_uniq', 'unique (zalo_id)', 'The zalo id must be unique !')]

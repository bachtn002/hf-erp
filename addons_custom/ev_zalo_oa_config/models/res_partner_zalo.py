# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartnerZalo(models.Model):
    _inherit = 'res.partner.zalo'

    oa_id = fields.Char('OA ID', required=True)
    app_id = fields.Char('APP ID', required=True)


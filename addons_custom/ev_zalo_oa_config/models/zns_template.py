# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ZNSTemplate(models.Model):
    _inherit = 'zns.template'

    oa_id = fields.Char('OA ID', required=True)

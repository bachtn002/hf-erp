# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ZNSTemplateParam(models.Model):
    _name = 'zns.template.param'
    _description = 'Zalo Notification Service Template Detail Params'
    _order = 'create_date desc'

    name = fields.Char('Name Param')
    require = fields.Boolean('Require')
    type = fields.Char('Type')
    max_length = fields.Integer('Max Length', default=0)
    min_length = fields.Integer('Min Length', default=0)
    accept_null = fields.Boolean('Accept Null', default=None)

    zns_template_id = fields.Many2one('zns.template', 'ZNS Template')

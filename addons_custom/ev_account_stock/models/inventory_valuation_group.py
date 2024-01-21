# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class InventoryValuationGroup(models.Model):
    _name = 'inventory.valuation.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char('Name')
    code = fields.Char('Code')
    sequence = fields.Integer('Sequence', default=10)

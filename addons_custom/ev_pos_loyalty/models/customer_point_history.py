# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CustomerPointHistory(models.Model):
    _name = 'customer.point.history'
    _order = 'create_date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer point history'

    partner_id = fields.Many2one('res.partner', string="Partner")
    point = fields.Float(string="Point")
    expire_date = fields.Date('Expire date')
    month_expire = fields.Integer('Month Expire')
    state = fields.Selection([
        ('available', 'Available'),
        ('expired', 'Expired')], string="State")
    

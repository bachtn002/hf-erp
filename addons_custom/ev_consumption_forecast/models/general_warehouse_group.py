# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'general.warehouse.group'

    order_schedule_ids = fields.Many2many('custom.weekdays', 'general_warehouse_weekdays_rel', 'general_warehouse_group_id', 'weekday_id',
                                            string='Order Schedule')



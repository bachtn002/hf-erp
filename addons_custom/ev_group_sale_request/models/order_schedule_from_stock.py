# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class OrderScheduleFromStock(models.Model):
    _name = 'order.schedule.from.stock'

    name = fields.Char('Name')
    general_warehouse_group_id = fields.Many2one('general.warehouse.group', 'General Warehouse Group')
    general_product_group_id = fields.Many2one('general.product.group', 'General Product Group')
    order_schedule_ids = fields.Many2many('custom.weekdays', 'order_schedule_weekdays_rel',
                                           'order_schedule_id', 'weekday_id', string='Order Schedule')

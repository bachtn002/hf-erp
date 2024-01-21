# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class CheckPromotionCodeLine(models.TransientModel):
    _name = 'check.promotion.code.line'

    check_promotion_code_id = fields.Many2one('check.promotion.code', 'Check Promotion Code')

    order_id = fields.Many2one('pos.order', 'Order')
    phone = fields.Char('Phone number')

# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class SaleOnlinePaymentInfo(models.Model):
    _name = 'sale.online.payment.info'
    _description = 'Sale Online Payment Info'

    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method Id')
    amount = fields.Float(string='Amount')
    sale_online_id = fields.Many2one('sale.online', string='Sale Online Order')
    domain_payment_method = fields.Many2many('pos.payment.method',
                                             related='sale_online_id.pos_config_id.payment_method_ids')
    domain_payment_method_channel = fields.Many2many('pos.payment.method',
                                                     related='sale_online_id.pos_channel_id.pos_payment_methods_ids')

    @api.onchange('amount')
    def _onchange_amount(self):
        for item in self:
            if item.amount < 0:
                raise ValidationError(_('You can not set amount negative.'))
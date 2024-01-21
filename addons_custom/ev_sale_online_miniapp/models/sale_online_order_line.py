# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import math


class SaleOnlineOrderLine(models.Model):
    _inherit = 'sale.online.order.line'

    x_is_price_promotion = fields.Float(string='Price Promotion', digits='Product Price')
    amount_promotion_loyalty = fields.Float(string='Amount Promotion Loyalty', digits='Product Price',
                                            compute='_compute_amount_promotion_loyalty', store=True)
    amount_promotion_total = fields.Float(string='Amount Promotion Total',
                                          compute='_compute_amount_promotion_total',
                                          digits='Product Price', store=True)
    promotion_code = fields.Char(string='Promotion Code')
    discount = fields.Float(string='Discount', digits='Product Price')
    amount_subtotal_incl = fields.Float(string='Amount Subtotal Incl', digits='Product Price')
    is_not_allow_editing = fields.Boolean(related='sale_online_id.is_not_allow_editing')
    amount = fields.Float(digits='Product Price')

    @api.onchange('product_id', 'quantity')
    @api.depends('product_id', 'quantity')
    def _compute_amount(self):
        for record in self:
            record._compute_price()
            record.amount = record.price * round(record.quantity, 3)
            record.amount_subtotal_incl = record.amount - record.discount

    @api.onchange('amount')
    def _onchange_amount(self):
        for item in self:
            item.amount_subtotal_incl = item.amount

    @api.onchange('amount_subtotal_incl')
    def _onchange_amount_subtotal_incl(self):
        for item in self:
            if item.amount_subtotal_incl < 0:
                raise ValidationError(_('You can not set amount subtotal incl negative.'))
            if item.amount_subtotal_incl > item.amount:
                raise ValidationError(_('Amount subtotal incl can not greater than amount'))
            item.discount = item.amount - item.amount_subtotal_incl
            item.x_is_price_promotion = item.discount

    @api.depends('sale_online_id.total_discount', 'sale_online_id.total_discount_on_bill')
    def _compute_amount_promotion_total(self):
        sum_price_product_before = 0
        vals = []
        for item in self:
            line_ids = self.env['sale.online.order.line'].sudo().search(
                [('sale_online_id', '=', item.sale_online_id.id)])
            vals.append(line_ids)
        _vals = list(set(vals))
        for item in _vals:
            if not item:
                _vals = self
                for k in self:
                    k.amount_promotion_total = 0
                    sum_price_product_before += (k.quantity * k.price) - k.x_is_price_promotion
                    self.calculate(self, sum_price_product_before)
                break
            sum_price_product_before = 0
            for i in item:
                i.amount_promotion_total = 0
                sum_price_product_before += (i.quantity * i.price) - i.x_is_price_promotion

            self.calculate(item, sum_price_product_before)

    def calculate(self, item, sum_price_product_before):
        if sum_price_product_before > 0:
            for zz in item:
                total_discount_on_bill = zz.sale_online_id.total_discount_on_bill
                loyalty_point_redeem = zz.sale_online_id.loyalty_point_redeem
                k = 0
                i = 0
                length_order_line = len(zz.sale_online_id.order_line_ids)
                total_discount_allocated = 0
                total_discount_allocate_reward = 0

                for line in zz.sale_online_id.order_line_ids:
                    k += 1
                    promotion_amount = line.x_is_price_promotion
                    discount = math.ceil(
                        (((line.quantity * line.price) - promotion_amount) * 100) / sum_price_product_before)
                    if total_discount_on_bill > 0 and total_discount_allocated < total_discount_on_bill:
                        total_discount = round(total_discount_on_bill * (discount / 100))
                        if total_discount > 0:
                            price_subtotal_incl = line.quantity * line.price
                            if k < length_order_line:
                                max_price_discount_allowed = price_subtotal_incl - promotion_amount
                                if total_discount > max_price_discount_allowed:
                                    total_discount = max_price_discount_allowed

                                total_discount_allocated = round(total_discount_allocated + total_discount)
                                if total_discount_allocated <= total_discount_on_bill:
                                    i = k
                                    line.amount_promotion_total = total_discount
                                else:
                                    i = k
                                    line.amount_promotion_total = total_discount_on_bill - (
                                            total_discount_allocated - total_discount)
                            if k == length_order_line:
                                i = k
                                line.amount_promotion_total = total_discount_on_bill - total_discount_allocated
                        else:
                            if total_discount_allocated < total_discount_on_bill and k == length_order_line:
                                tmp_discount = total_discount_on_bill - total_discount_allocated
                                zz.sale_online_id.order_line_ids[i - 1].amount_promotion_total = \
                                    zz.sale_online_id.order_line_ids[i - 1].amount_promotion_total + tmp_discount

    @api.depends('sale_online_id.total_discount', 'sale_online_id.loyalty_point_redeem')
    def _compute_amount_promotion_loyalty(self):
        sum_price_product_before = 0
        vals = []
        for item in self:
            line_ids = self.env['sale.online.order.line'].sudo().search(
                [('sale_online_id', '=', item.sale_online_id.id)])
            vals.append(line_ids)
        _vals = list(set(vals))
        for item in _vals:
            if not item:
                _vals = self
                for k in self:
                    k.amount_promotion_loyalty = 0
                    sum_price_product_before += (k.quantity * k.price) - k.x_is_price_promotion
                    self.calculate(self, sum_price_product_before)
                break
            sum_price_product_before = 0
            for i in item:
                i.amount_promotion_loyalty = 0
                sum_price_product_before += (i.quantity * i.price) - i.x_is_price_promotion

            self.calculate_loyalty(item, sum_price_product_before)

    def calculate_loyalty(self, item, sum_price_product_before):
        if sum_price_product_before > 0:
            for z in item:
                total_discount_on_bill = z.sale_online_id.total_discount_on_bill
                loyalty_point_redeem = z.sale_online_id.loyalty_point_redeem
                k = 0
                i = 0
                length_order_line = len(z.sale_online_id.order_line_ids)
                total_discount_allocated = 0
                total_discount_allocate_reward = 0

                for line in z.sale_online_id.order_line_ids:
                    k += 1
                    promotion_amount = line.x_is_price_promotion
                    discount = math.ceil(
                        (((line.quantity * line.price) - promotion_amount) * 100) / sum_price_product_before)

                    if loyalty_point_redeem > 0 and total_discount_allocated < loyalty_point_redeem:
                        max_discount_reward_allowed = (
                                                              line.quantity * line.price) - promotion_amount - line.amount_promotion_total
                        if max_discount_reward_allowed < 0:
                            max_discount_reward_allowed = 0
                        total_discount_reward = round(loyalty_point_redeem * (discount / 100))
                        if total_discount_reward > max_discount_reward_allowed:
                            total_discount_reward = max_discount_reward_allowed
                        total_discount_allocate_reward = round(total_discount_allocate_reward + total_discount_reward)
                        if total_discount_allocate_reward < loyalty_point_redeem and k < length_order_line:
                            line.amount_promotion_loyalty = total_discount_reward
                        else:
                            tmp_discount = loyalty_point_redeem - (
                                    total_discount_allocate_reward - total_discount_reward)
                            if tmp_discount > 0:
                                line.amount_promotion_loyalty = tmp_discount

    def _compute_price(self):
        for record in self:
            if not record.sale_online_id.is_created_by_api:
                record.price = 0
                pricelist_item = self.env['product.pricelist.item'].sudo().search(
                    [('pricelist_id', '=', record.sale_online_id.price_list_id.id),
                     ('product_tmpl_id', '=', record.product_id.id), '|', ('date_end', '=', False),
                     ('date_end', '>=', datetime.today()), '|', ('date_start', '=', False),
                     ('date_start', '<=', datetime.today())], limit=1)
                if pricelist_item:
                    price_unit = pricelist_item.fixed_price
                else:
                    price_unit = record.product_id.list_price
                record.price = price_unit

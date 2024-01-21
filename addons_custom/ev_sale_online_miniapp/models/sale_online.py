# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class SaleOnline(models.Model):
    _inherit = 'sale.online'

    amount_total_before_discount = fields.Float(string='Amount Total Before Discount', compute='_compute_amount_total')
    amount_total = fields.Float(string='Amount Total', compute='_compute_amount_total')
    sinvoice_vat = fields.Char(string='SInvoice Vat')
    sinvoice_company_name = fields.Char(string='SInvoice Company Name')
    sinvoice_address = fields.Char(string='SInvoice Address')
    sinvoice_email = fields.Char(string='SInvoice Email')
    buyer_not_get_invoice = fields.Boolean(string='Buyer Not Get Invoice', default=True)
    ref_order = fields.Char(string='Ref Order')
    payment_method_ids = fields.One2many('sale.online.payment.info', 'sale_online_id', string='Payment Methods')
    is_created_by_api = fields.Boolean(string='Is Created Api')
    loyalty_point_redeem = fields.Integer(string='Loyalty Point Redeem', default=0)
    sale_online_discount_ids = fields.One2many('sale.online.discount', 'sale_online_id', string='Sale Online Discounts')
    discount_on_prod_ids = fields.One2many('sale.online.discount.on.product', 'sale_online_id',
                                           string='Discounts On Product')
    total_discount = fields.Float(string='Total Discount', compute='_compute_amount_total')
    total_discount_on_bill = fields.Float(string='Total Discount On Bill', default=0)
    promotion_code = fields.Char(string='Promotion Code')
    cancel_reason = fields.Char(string='Cancel Reason')
    is_not_allow_editing = fields.Boolean()

    _sql_constraints = [
        ('unique_ref_order', 'UNIQUE(ref_order)', 'Field ref_order must be unique!')
    ]

    @api.constrains('is_created_by_api', 'ref_order')
    def _check_ref_order(self):
        for item in self:
            if item.is_created_by_api:
                if not item.ref_order:
                    raise ValidationError('Ref order required.')
                sale_online = self.env['sale.online'].search(
                    [('is_created_by_api', '=', True), ('ref_order', '=', item.ref_order), ('id', '!=', item.id)])
                if sale_online:
                    raise ValidationError('Ref order already exists.')

    @api.model
    def sync_orders_online(self, config_id, fields):
        res = super(SaleOnline, self).sync_orders_online(config_id, fields)
        for item in res:
            sale_online = self.env['sale.online'].search([('name', '=', item['name']), ('pos_channel_id', '!=', False)])
            payment_info = []
            for i in sale_online.payment_method_ids:
                payment_info.append([i.payment_method_id.id, i.amount])
            buyer_ngi = sale_online.buyer_not_get_invoice
            buyer_not_get_invoice = 11  # Có lấy hoá đơn
            if buyer_ngi:
                buyer_not_get_invoice = 22  # Không lấy hoá đơn
            item.update({
                'loyalty_point_redeem': sale_online.loyalty_point_redeem,
                'is_created_by_api': sale_online.is_created_by_api,
                'payment_method_ids': sale_online.payment_method_ids,
                'payment_info': payment_info,
                'sinvoice_vat': sale_online.sinvoice_vat if not buyer_ngi else '',
                'sinvoice_company_name': sale_online.sinvoice_company_name if not buyer_ngi else '',
                'sinvoice_address': sale_online.sinvoice_address if not buyer_ngi else '',
                'sinvoice_email': sale_online.sinvoice_email if not buyer_ngi else '',
                'buyer_not_get_invoice': buyer_not_get_invoice,
                'write_date': sale_online.write_date.strftime('%Y-%m-%d %H:%M:%S') if sale_online.write_date else '',
                'id_sale_online': sale_online.id,
                'state_sale_online': sale_online.state,
                'total_discount_on_bill': sale_online.total_discount_on_bill,
            })
            product_km = self.env['product.product'].sudo().search([('default_code', '=', 'KM')], limit=1)
            if sale_online.total_discount_on_bill > 0:
                item.update({
                    'product_km_id': product_km.id,
                })
            order_line_info = []
            for ol in sale_online.order_line_ids:
                order_line_info.append([
                    ol.product_id.id,
                    product_km.id,
                    ol.promotion_code,
                    ol.discount,
                    ol.x_is_price_promotion,
                    ol.amount_promotion_loyalty,
                    ol.amount_promotion_total
                ])
            item.update({
                'order_line_info': order_line_info
            })
            sale_online_discount_on_bill = []
            sale_online_discount_on_product = []

            for i in sale_online.sale_online_discount_ids:
                if i.discount_type == 'on_bill':
                    sale_online_discount_on_bill.append({
                        'discount': i.discount_amount,
                        'promotion_code': i.promotion_code,
                        'promotion_id': i.promotion_id.id if i.promotion_id else '',
                        'product_id': product_km.id,
                        'x_product_promotion': self.env['pos.promotion'].search(
                            [('id', '=', i.promotion_id.id)]).name if i.promotion_id else '',
                    })
                if i.discount_type == 'on_product':
                    sale_online_discount_on_product.append({
                        'discount': i.discount_amount,
                        'promotion_code': i.promotion_code,
                        'product_code': i.product_code,
                        'promotion_id': i.promotion_id.id if i.promotion_id else '',
                        'product_id': product_km.id,
                        'x_product_promotion': self.env['pos.promotion'].search(
                            [('id', '=', i.promotion_id.id)]).name if i.promotion_id else '',
                    })
            item.update({
                'discount_on_bill': sale_online_discount_on_bill
            })
            item.update({
                'discount_on_product': sale_online_discount_on_product
            })
        return res

    @api.depends('order_line_ids', 'order_line_ids.amount', 'total_discount_on_bill')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total_before_discount = 0
            record.amount_total = 0
            record.total_discount = 0
            for r in record.order_line_ids:
                record.amount_total_before_discount += r.amount
                record.amount_total += r.amount_subtotal_incl
                record.total_discount += r.discount
            record.total_discount += record.total_discount_on_bill
            record.amount_total -= (record.total_discount_on_bill + record.loyalty_point_redeem)

    @api.onchange('total_discount_on_bill')
    def _onchange_check_total_discount_on_bill(self):
        for item in self:
            if item.total_discount_on_bill < 0:
                raise ValidationError(_('You can not set total discount on bill negative.'))
            max_total_allowed_discount = 0
            for line in item.order_line_ids:
                max_total_allowed_discount += line.amount_subtotal_incl
            max_total_allowed_discount -= item.loyalty_point_redeem
            if item.total_discount_on_bill > max_total_allowed_discount:
                raise ValidationError(_('Cannot enter a discount greater than the total amount.'))

    def check_state_sale_online(self, id, total_with_tax, write_date):
        sale_on = self.env['sale.online'].search([('id', '=', id)])
        res = [True, True]
        if sale_on.write_date.strftime('%Y-%m-%d %H:%M:%S') != write_date:
            res[0] = False
        if round(float(sale_on.amount_total)) != float(total_with_tax):
            res[1] = False
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if self.is_created_by_api:
            raise ValidationError(_('You can not copy sale online is created by api!'))
        return super(SaleOnline, self).copy(default)

    @api.constrains('payment_method_ids', 'amount_total')
    def _check_amount_total_payment(self):
        for record in self:
            total = sum(payment.amount for payment in record.payment_method_ids)
            if total > self.amount_total:
                raise ValidationError(_('Total amount in payment method greater than Amount total!'))

    @api.onchange('pos_channel_id')
    def change_pos_channel_id(self):
        self.is_not_allow_editing = self.pos_channel_id.is_not_allow_editing
        if not self.pos_channel_id.is_not_allow_editing:
            for line in self.order_line_ids:
                line.amount_subtotal_incl = line.amount
            self.total_discount_on_bill = 0

    def write(self, vals):
        if self.is_created_by_api and self.home_delivery:
            if 'lat' in vals:
                vals.pop('lat')
            if 'long' in vals:
                vals.pop('long')
            if 'x_distance' in vals:
                vals.pop('x_distance')
            if 'address_delivery' in vals:
                vals.pop('address_delivery')
            if vals == {}:
                return
        return super(SaleOnline, self).write(vals)

    def cancel_sale_online(self):
        for record in self:
            if record.state == 'finish':
                record.state = 'finish'
            else:
                record.state = 'cancel'

    def send_sale_request(self):
        for item in self:
            item.action_allocate_discount()

            _total_amount_promotion_total = 0
            _total_amount_promotion_loyalty = 0
            for p in item.order_line_ids:
                _total_amount_promotion_total += p.amount_promotion_total
                _total_amount_promotion_loyalty += p.amount_promotion_loyalty
            if _total_amount_promotion_total != item.total_discount_on_bill:
                raise ValidationError(_('Discount allocation is not accurate.'))
            if _total_amount_promotion_loyalty != item.loyalty_point_redeem:
                raise ValidationError(_('Accumulated points allocation is not accurate.'))
        return super(SaleOnline, self).send_sale_request()

    def action_allocate_discount(self):
        for item in self.order_line_ids:
            item._compute_amount_promotion_total()
            item._compute_amount_promotion_loyalty()

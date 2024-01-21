# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PromotionReport(models.TransientModel):
    _name = 'promotion.report'

    name = fields.Char(default="Báo cáo chương trình xúc tiến bán")
    from_date = fields.Date('Form date',default=fields.Date.today())
    to_date = fields.Date('To date',default=fields.Date.today())
    pos_config_id = fields.Many2one('pos.config','Shop')
    promotion_config_id = fields.Many2one('promotion.config', 'Promotion')
    pos_session_id = fields.Many2one('pos.session','Session')
    total_amount = fields.Float('Total amount')
    total_quantity = fields.Float('Total Quantity')
    total_discount = fields.Float('Total Discount')
    promotion_lines = fields.One2many('promotion.report.line', 'promotion_report_id', 'Lines')

    
    def action_filter_all(self):
        self.total_amount = 0
        self.total_quantity = 0
        self.total_discount = 0
        self.promotion_lines.unlink()

        if self.pos_config_id:
            if self.promotion_config_id.id != False:
                pos_order_line_ids = self.env['pos.order.line'].search(
                    [('order_id.date_order', '>=', self.from_date), ('order_id.date_order', '<=', self.to_date),
                     ('order_id.session_id.config_id', '=', self.pos_config_id.id),
                     ('promotion_id','=',self.promotion_config_id.id)])
            else:
                pos_order_line_ids = self.env['pos.order.line'].search(
                    [('order_id.date_order', '>=', self.from_date), ('order_id.date_order', '<=', self.to_date),
                     ('order_id.session_id.config_id', '=', self.pos_config_id.id)])
        else:
            if self.promotion_config_id.id != False:
                pos_order_line_ids = self.env['pos.order.line'].search(
                    [('order_id.date_order', '>=', self.from_date), ('order_id.date_order', '<=', self.to_date),
                     ('promotion_id','=',self.promotion_config_id.id)])
            else:
                pos_order_line_ids = self.env['pos.order.line'].search(
                    [('order_id.date_order', '>=', self.from_date), ('order_id.date_order', '<=', self.to_date)])
        if len(pos_order_line_ids) <= 0:
            return
        order_line_args = []
        amount_total = 0
        total_quantity = 0
        total_discount = 0
        for line in pos_order_line_ids:
            if line.promotion_id.id != False:
                pos_order_line = {
                    'order_id': line.order_id.id,
                    'customer_id': line.order_id.partner_id.id,
                    'product_id': line.product_id.id,
                    'price_unit': line.product_id.lst_price,
                    'quantity': line.qty,
                    'amount_discount': (line.product_id.lst_price * line.qty) - line.price_subtotal,
                    'amount_total': line.price_subtotal,
                    'promotion_report_id': self.id,
                    'name_discount': line.promotion_id.name
                }
                order_line_args.append(pos_order_line)
                total_quantity += line.qty
                amount_total += abs(line.price_subtotal)
                total_discount += ((line.product_id.lst_price * line.qty) - line.price_subtotal)
        self.total_discount = total_discount
        self.total_quantity = total_quantity
        self.total_amount = amount_total
        self.promotion_lines = order_line_args

class PromotionReportLine(models.TransientModel):
    _name = 'promotion.report.line'

    promotion_report_id = fields.Many2one('promotion.report','Pos report')
    order_id = fields.Many2one('pos.order', 'Order')
    product_id = fields.Many2one('product.product','Product')
    customer_id = fields.Many2one('res.partner', 'Customer')
    price_unit = fields.Float('Price unit')
    quantity = fields.Float('Quantity')
    amount_discount = fields.Float('Amount discount')
    amount_total = fields.Float('Amount total')
    name_discount = fields.Char('Name discount')
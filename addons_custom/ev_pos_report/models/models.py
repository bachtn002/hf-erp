# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class IZIPosReport(models.TransientModel):
    _name = 'pos.order.report'

    name = fields.Char(default="Báo cáo bán lẻ")
    from_date = fields.Date('From date', default=fields.Date.today())
    to_date = fields.Date('To date', default=fields.Date.today())
    pos_config_id = fields.Many2one('pos.config', 'Shop')
    pos_session_id = fields.Many2one('pos.session', 'Session')
    payment_method_id = fields.Many2one('pos.payment.method', 'Payment Method')
    # new pos shop id
    pos_shop_id = fields.Many2one('pos.shop', 'Shop')
    # source_id = fields.Many2one('utm.source', 'Source')
    user_id = fields.Many2one('res.users', 'Saleman')
    # Qty
    total_quantity = fields.Float('Total Qty')
    total_quantity_refund = fields.Float('Total Qty Refund')
    total_quantity_sale = fields.Float('Total Qty Sale')
    # Amount
    total_amount = fields.Float('Amount Total')
    total_amount_refund = fields.Float('Amount Total Refund')
    total_amount_sale = fields.Float('Amount Total Sale')
    # Total order
    total_order = fields.Float('Total Order')
    total_order_refund = fields.Float('Total Order Refund')
    total_order_sale = fields.Float('Total Order Sale')
    # Payment
    payment_cash = fields.Float('Payment Cash')
    payment_bank = fields.Float('Payment Card')
    payment_other = fields.Float('Payment Other')
    report_type = fields.Selection(
        [('order', 'Order'), ('order_line', 'Order line'),
         ('product', 'Product'), ('categories', 'Categories'), ('user', 'Saleman'),
         ('payment_method', 'Payment Method')]
        , default='order')

    order_lines = fields.One2many('report.order', 'pos_report_id', 'Order')
    order_line_lines = fields.One2many('report.order.line', 'pos_report_id', 'Order line')
    product_lines = fields.One2many('report.order.product', 'pos_report_id', 'Products')
    product_categories_lines = fields.One2many('report.order.product.categories', 'pos_report_id', 'Product Categories')
    user_lines = fields.One2many('report.order.user', 'pos_report_id', 'Saleman')
    payment_method_lines = fields.One2many('report.order.payment.method', 'pos_report_id', 'Payment Method')
    payment_lines = fields.One2many('report.order.payment', 'pos_report_id', 'Payments')

    # Cho phép chọn tất cả cửa hàng (chỉ với báo cáo hình thức thanh toán)
    x_full_pos = fields.Boolean('Select full pos', default=False)

    payment_method_cash = fields.Boolean('Select all cash', default=False)

    # action all
    def print_pos_order_xlsx(self):
        for record in self:
            if record.report_type == 'order':
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/report/xlsx/ev_pos_report.pos_order_xlsx/%s' % (self.id),
                    'target': 'new',
                    'res_id': self.id,
                }
            if record.report_type == 'order_line':
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/report/xlsx/ev_pos_report.pos_order_line_xlsx/%s' % (self.id),
                    'target': 'new',
                    'res_id': self.id,
                }
            if record.report_type == 'payment_method':
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/report/xlsx/ev_pos_report.pos_order_payment_method_xlsx/%s' % (self.id),
                    'target': 'new',
                    'res_id': self.id,
                }

    def action_filter_all(self):
        # Set default 0
        # Qty
        self.total_quantity = 0
        self.total_quantity_refund = 0
        self.total_quantity_sale = 0
        # Amount
        self.total_amount = 0
        self.total_amount_refund = 0
        self.total_amount_sale = 0
        # Total order
        self.total_order = 0
        self.total_order_refund = 0
        self.total_order_sale = 0
        # Payment
        self.payment_cash = 0
        self.payment_bank = 0
        self.payment_other = 0

        self.order_lines.unlink()
        self.order_line_lines.unlink()
        self.product_categories_lines.unlink()
        self.product_lines.unlink()
        self.user_lines.unlink()
        self.payment_lines.unlink()
        self.payment_method_lines.unlink()

        if self.report_type == 'payment_method':
            order_payment_method = []
            pos_order_ids = []
            payment_method_ids = []
            if self.payment_method_cash:
                payment_methods = self.env['pos.payment.method'].search([('is_cash_count', '=', True)])
                if payment_methods:
                    for payment_method in payment_methods:
                        payment_method_ids.append(payment_method.id)
            else:
                if self.payment_method_id:
                    payment_method_ids.append(self.payment_method_id.id)
                else:
                    payment_method_ids = False
            payment_order_ids = self._report_orders_payment(self.from_date, self.to_date, self.pos_shop_id.id,
                                                            payment_method_ids)

            if len(payment_order_ids) < 1:
                return

            for payment_order in payment_order_ids:
                pos_order = {
                    'order_id': payment_order.pos_order_id.id,
                    'customer_id': payment_order.pos_order_id.partner_id.id,
                    'user_id': payment_order.pos_order_id.user_id.id,
                    'date': payment_order.pos_order_id.date_order,
                    'pos_report_id': self.id,
                    'payment_method_id': payment_order.payment_method_id.id,
                    'amount_payment': payment_order.amount,
                    'x_pos_shop_id': payment_order.x_pos_shop_id.id,
                    'pos_channel_id': payment_order.pos_order_id.pos_channel_id.id
                }

                order_payment_method.append((0, 0, pos_order))
                pos_order_ids.append(payment_order.pos_order_id.id)
            self.payment_method_lines = order_payment_method

            for line in self.payment_method_lines:
                if line.amount_payment < 0:
                    self.total_amount_refund += line.amount_payment
                else:
                    self.total_amount_sale += line.amount_payment
                self.total_amount += line.amount_payment

            # Tính số lượng đơn, số lượng trả, bán
            pos_orders = self.env['pos.order'].search([('id', 'in', pos_order_ids)])
            amount_refund = 0
            amount_sale = 0
            if pos_orders:
                for order in pos_orders:
                    self.total_order += 1
                    if order.x_pos_order_refund_id:
                        self.total_order_refund += 1
                    else:
                        self.total_order_sale += 1
                    for line in order.lines:
                        if line.price_unit >= 0:
                            if order.id != False:
                                if order.x_pos_order_refund_id:
                                    self.total_quantity_refund += line.qty
                                else:
                                    self.total_quantity_sale += line.qty
                            self.total_quantity += line.qty
        else:
            pos_orders = self._report_orders(self.from_date, self.to_date, self.pos_shop_id.id)

            if len(pos_orders) < 1:
                return

            order_line_lines = []
            order_ids = []

            for order in pos_orders:
                if order.id != False:
                    if order.x_pos_order_refund_id:
                        self.total_order_refund += 1
                        self.total_amount_refund += order.amount_total
                    else:
                        self.total_amount_sale += order.amount_total
                        self.total_order_sale += 1

                self.total_order += 1

                quantity = 0
                saleman_total_quantity = 0
                for line in order.lines:
                    if line.price_unit >= 0:
                        quantity += line.qty
                        if order.id != False:
                            if order.x_pos_order_refund_id:
                                self.total_quantity_refund += line.qty
                                saleman_total_quantity += line.qty
                            else:
                                self.total_quantity_sale += line.qty
                                saleman_total_quantity += line.qty
                        self.total_quantity += line.qty

                        # Sản phẩm
                        if self.report_type == 'product':
                            product_id = self.env['report.order.product'].search(
                                [('pos_report_id', '=', self.id), ('product_id', '=', line.product_id.id),
                                 ('price_unit', '=', line.price_unit),
                                 ('sale_staff', '=', order.user_id.id)], limit=1)

                            if product_id.id == False:
                                self.env['report.order.product'].create({
                                    'pos_report_id': self.id,
                                    'product_id': line.product_id.id,
                                    'quantity': line.qty,
                                    'price_unit': line.price_unit,
                                    'discount': (line.price_unit * line.qty) * (line.discount / 100),
                                    'amount_total': line.price_subtotal_incl,
                                    'category_id': line.product_id.product_tmpl_id.categ_id.id,
                                    'sale_staff': order.user_id.id,
                                })
                            else:
                                product_id.update({
                                    'quantity': product_id.quantity + line.qty,
                                    'discount': product_id.discount + (line.price_unit * line.qty) * (
                                            line.discount / 100),
                                    'amount_total': product_id.amount_total + line.price_subtotal_incl,
                                })
                                if product_id.quantity == 0:
                                    product_id.unlink()

                        # Nhóm sản phẩm
                        if self.report_type == 'categories':
                            product_category = self.env['report.order.product.categories'].search(
                                [('pos_report_id', '=', self.id),
                                 ('category_id', '=', line.product_id.product_tmpl_id.categ_id.id)],
                                limit=1)
                            if product_category.id == False:
                                self.env['report.order.product.categories'].create({
                                    'pos_report_id': self.id,
                                    'category_id': line.product_id.product_tmpl_id.categ_id.id,
                                    'quantity': line.qty,
                                    'amount_total': line.price_subtotal_incl
                                })
                            else:
                                product_category.update({
                                    'quantity': product_category.quantity + line.qty,
                                    'amount_total': product_category.amount_total + line.price_subtotal_incl,
                                })

                    # Chi tiết đơn hàng
                    if self.report_type == 'order_line':
                        discount = 0
                        if line.discount > 0:
                            discount = (line.qty * line.price_unit) * (line.discount / 100)
                        amount_total = (line.qty * line.price_unit) - discount

                        pos_order_line = {
                            'order_id': order.id,
                            'customer_id': order.partner_id.id,
                            'phone': order.partner_id.phone,
                            'product_id': line.product_id.id,
                            'price_unit': line.price_unit,
                            'quantity': line.qty,
                            'discount': discount,
                            'amount_total': amount_total,
                            'pos_report_id': self.id,
                        }
                        order_line_lines.append((0, 0, pos_order_line))

                self.total_amount = self.total_amount_refund + self.total_amount_sale

                if self.report_type == 'order':
                    # for payment_order in order.payment_ids:
                    #     report_order = self.env['report.order'].search([('order_id','=', order.id),('pos_report_id','=',self.id),
                    #                                                     ('payment_method_id','=',payment_order.payment_method_id.id)], limit=1)
                    #     if report_order:
                    #         report_order.update({
                    #             'amount_payment': report_order.amount_payment + payment_order.amount
                    #         })
                    #     else:
                    pos_order = {
                        'order_id': order.id,
                        'customer_id': order.partner_id.id,
                        'amount_total': order.amount_total,
                        'user_id': order.user_id.id,
                        'date': order.date_order,
                        'pos_report_id': self.id,
                        'quantity': quantity,
                        'note': order.note
                        # 'payment_method_id': payment_order.payment_method_id.id,
                        # 'amount_payment': payment_order.amount
                    }
                    # self.env['report.order'].create(pos_order)
                    order_ids.append((0, 0, pos_order))

                if self.report_type == 'user':
                    user = self.env['report.order.user'].search(
                        [('pos_report_id', '=', self.id),
                         ('user_id', '=', order.user_id.id)],
                        limit=1)
                    if user.id == False:
                        self.env['report.order.user'].create({
                            'pos_report_id': self.id,
                            'user_id': order.user_id.id,
                            'total_order': 1,
                            'total_quantity': saleman_total_quantity,
                            'amount_total': order.amount_total,
                        })
                    else:
                        user.update({
                            'total_order': user.total_order + 1,
                            'total_quantity': user.total_quantity + saleman_total_quantity,
                            'amount_total': user.amount_total + order.amount_total,
                        })

                for payment in order.payment_ids:
                    if payment:
                        payment_id = self.env['report.order.payment'].search([
                            ('pos_report_id', '=', self.id),
                            ('payment_method_id', '=', payment.payment_method_id.id),
                        ], limit=1)
                        if not payment_id:
                            self.env['report.order.payment'].create({
                                'pos_report_id': self.id,
                                'payment_method_id': payment.payment_method_id.id,
                                'amount': payment.amount,
                                'pos_amount_currency': payment.amount,
                            })
                        else:
                            payment_id.update({
                                'amount': payment_id.amount + payment.amount,
                            })
            self.order_lines = order_ids
            self.order_line_lines = order_line_lines

    def _report_orders(self, from_date, to_date, pos_shop_id=False):
        # from_date = from_date.strftime('%Y-%m-%d %H:%M:%S')
        # to_date = to_date.strftime('%Y-%m-%d %H:%M:%S')
        # from_date = (datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
        # to_date = (datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
        if not self.x_full_pos:
            args = []
            if pos_shop_id != False:
                args += [('session_id.x_pos_shop_id', '=', pos_shop_id)]
            pos_order_ids = self.env['pos.order'].sudo().search(
                [('date_order', '>=', from_date - relativedelta(hours=7)),
                 ('date_order', '<=', to_date + relativedelta(hours=17)),
                 ('state', 'not in', ('draft', 'cancel'))] + args, order='date_order')
        else:
            pos_order_ids = self.env['pos.order'].sudo().search(
                [('date_order', '>=', from_date - relativedelta(hours=7)),
                 ('date_order', '<=', to_date + relativedelta(hours=17)),
                 ('state', 'not in', ('draft', 'cancel'))], order='date_order')
        return pos_order_ids

    def _report_orders_payment(self, from_date, to_date, pos_shop_id=False, payment_method_id=False):
        if not self.x_full_pos:
            args = []
            if pos_shop_id != False:
                args += [('pos_order_id.session_id.x_pos_shop_id', '=', pos_shop_id)]

            if payment_method_id != False:
                args += [('payment_method_id', 'in', payment_method_id)]

            pos_payment_ids = self.env['pos.payment'].sudo().search(
                [('pos_order_id.date_order', '>=', from_date - relativedelta(hours=7)),
                 ('pos_order_id.date_order', '<=', to_date + relativedelta(hours=17)),
                 ('pos_order_id.state', 'not in', ('draft', 'cancel'))] + args, order='payment_date')
        else:
            args = []
            if payment_method_id != False:
                args += [('payment_method_id', 'in', payment_method_id)]
            pos_payment_ids = self.env['pos.payment'].sudo().search(
                [('pos_order_id.date_order', '>=', from_date - relativedelta(hours=7)),
                 ('pos_order_id.date_order', '<=', to_date + relativedelta(hours=17)),
                 ('pos_order_id.state', 'not in', ('draft', 'cancel'))] + args, order='payment_date')
        return pos_payment_ids

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type != 'payment_method':
            self.x_full_pos = False


class ReportOrder(models.TransientModel):
    _name = 'report.order'

    order_id = fields.Many2one('pos.order', 'Order')
    customer_id = fields.Many2one('res.partner', 'Customer')
    amount_total = fields.Float('Amount total')
    user_id = fields.Many2one('res.users', 'Saleman')
    date = fields.Datetime('Date')
    quantity = fields.Float('Quantity')
    source_id = fields.Many2one('utm.source', 'Source')
    pos_report_id = fields.Many2one('pos.order.report', 'Pos report')
    note = fields.Char('Note')
    order_refund_id = fields.Many2one('pos.order', 'Order Refund')
    # payment_method_id = fields.Many2one('pos.payment.method', 'Payment Method')
    # amount_payment = fields.Float('Amount Payment')


class ReportOrderLine(models.TransientModel):
    _name = 'report.order.line'

    pos_report_id = fields.Many2one('pos.order.report', 'Pos report')
    order_id = fields.Many2one('pos.order', 'Order')
    customer_id = fields.Many2one('res.partner', 'Customer')
    product_id = fields.Many2one('product.product', 'Product')
    lot_name = fields.Char('Lot Name')
    phone = fields.Char('Phone')
    price_unit = fields.Float('Price unit')
    quantity = fields.Float('Quantity')
    discount = fields.Float('Discount')
    name_discount = fields.Char('Name Discount')
    amount_total = fields.Float('Amount total')
    order_refund_id = fields.Many2one('pos.order', 'Order')


class ReportOrderProduct(models.TransientModel):
    _name = 'report.order.product'

    pos_report_id = fields.Many2one('pos.order.report', 'Pos report')
    category_id = fields.Many2one('product.category', 'Category')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    price_unit = fields.Float('Price Unit')
    discount = fields.Float('Discount')
    amount_total = fields.Float('Amount Total')
    sale_staff = fields.Many2one('res.users', 'Sale Staff')


class ReportOrderProductCategories(models.TransientModel):
    _name = 'report.order.product.categories'

    pos_report_id = fields.Many2one('pos.order.report', 'Pos Report')
    category_id = fields.Many2one('product.category', 'Category')
    quantity = fields.Float('Quantity')
    amount_total = fields.Float('Amount Total')


class ReportOrderUser(models.TransientModel):
    _name = 'report.order.user'

    pos_report_id = fields.Many2one('pos.order.report', 'Pos report')
    user_id = fields.Many2one('res.users', 'Saleman')
    total_order = fields.Float('Total Order')
    total_quantity = fields.Float('Total Quantity')
    amount_total = fields.Float('Amount Total')


class ReportOrderPayment(models.TransientModel):
    _name = 'report.order.payment'

    pos_report_id = fields.Many2one('pos.order.report', 'Pos Report')
    payment_method_id = fields.Many2one('pos.payment.method', 'Payment Method')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    pos_amount_currency = fields.Float('Amount Currency')
    rate = fields.Float('Rate')


class ReportOrderPaymentMethod(models.TransientModel):
    _name = 'report.order.payment.method'

    pos_report_id = fields.Many2one('pos.order.report', 'Pos report')
    order_id = fields.Many2one('pos.order', 'Order')
    customer_id = fields.Many2one('res.partner', 'Customer')
    amount_total = fields.Float('Amount total')
    user_id = fields.Many2one('res.users', 'Salexman')
    date = fields.Datetime('Date')
    quantity = fields.Float('Quantity')
    source_id = fields.Many2one('utm.source', 'Source')
    order_refund_id = fields.Many2one('pos.order', 'Order Refund')
    payment_method_id = fields.Many2one('pos.payment.method', 'Payment Method')
    amount_payment = fields.Float('Amount Payment')
    x_pos_shop_id = fields.Many2one('pos.shop', 'Shop')
    pos_channel_id = fields.Many2one('pos.channel', 'Pos Channel')

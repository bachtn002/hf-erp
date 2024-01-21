# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

from datetime import datetime

_logger = logging.getLogger(__name__)


class SaleOnline(models.Model):
    _name = 'sale.online'
    _inherit = ['mail.thread']

    name = fields.Char(string='name', readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='date', default=fields.Date.today)

    pos_config_id = fields.Many2one('pos.config', string='Pos Config')
    price_list_id = fields.Many2one('product.pricelist', string='Default Pricelist',
                                    related='pos_config_id.pricelist_id')
    item_ids = fields.One2many('product.pricelist.item', 'pricelist_id', related='price_list_id.item_ids')

    pos_order_id = fields.Many2one('pos.order', string='Pos order', readonly=True)

    order_line_ids = fields.One2many('sale.online.order.line', 'sale_online_id', string='List order')

    amount_total = fields.Float(string='Amount Total', compute='_compute_amount_total')
    qty_total = fields.Float(string='Quantity Total', compute='_compute_qty_total', digits='Product Unit of Measure')

    customer = fields.Char(string='Customer Name')
    phone = fields.Char(string='Phone')
    address = fields.Char(string='Address')
    note = fields.Text(string='Note')
    description = fields.Text('Description')
    partner_id = fields.Many2one('res.partner', 'Customer')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('finish', 'Finish'),
        ('cancel', 'Cancel')],
        string='state', default='draft', track_visibility='onchange'
    )

    _sql_constraints = [
        ('name_unique',
         'unique(name)',
         'Order number must be unique!')
    ]

    def create_customer(self):
        if self.partner_id.id != False:
            raise UserError(_('Customer has been created'))
        if len(self.phone) > 10:
            raise UserError(_('Phone number must be 10 characters'))
        partner_args = {
            'name': self.customer,
            'phone': self.phone,
            'id': False,
            'street': self.address,
        }
        partner = self.env['res.partner'].create_from_ui(partner_args)
        self.partner_id = partner

    @api.onchange('phone')
    def _onchange_phone(self):
        if self.phone != False:
            customer_id = self.env['res.partner'].search([('phone', '=', self.phone)], limit=1)
            if customer_id.id != False:
                self.customer = customer_id.name
                self.partner_id = customer_id.id
                self.address = customer_id.street
            else:
                self.customer = ''
                self.partner_id = False
                self.address = ''

    @api.depends('order_line_ids', 'order_line_ids.amount')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = 0
            for r in record.order_line_ids:
                record.amount_total += r.amount

    @api.depends('order_line_ids', 'order_line_ids.quantity')
    def _compute_qty_total(self):
        for record in self:
            record.qty_total = 0
            for r in record.order_line_ids:
                record.qty_total += r.quantity

    def set_to_draft(self):
        for record in self:
            if record.state == 'finish':
                return
            record.state = 'draft'

    def send_sale_request(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'sent'

    @api.model
    def sync_orders_online(self, config_id, fields):
        order_ids = self.env['sale.online'].search([('pos_config_id', '=', config_id), ('state', '=', 'sent')])
        orders = []

        for order in order_ids:
            lines = []
            for line in order.order_line_ids:
                product = self.env['product.product'].search_read(domain=[('product_tmpl_id', '=', line.product_id.id)],
                                                                  fields=fields)
                product_id = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)], limit=1)
                product_combos = self.env['product.combo'].search([('product_tmpl_id', '=', line.product_id.id)])
                line = {
                    'product_id': product_id.id,
                    'price': line.price,
                    'amount': line.amount,
                    'uom': line.uom.id,
                    'product_uom_category_id': line.product_uom_category_id.id,
                    'quantity': line.quantity,
                    'sale_online_id': line.sale_online_id.id,
                    'product': product,
                }
                lines.append(line)
                # nếu sp online là combo thì load thêm thành phần
                if len(product_combos) > 0:
                    for product in product_combos:
                        line = {
                            'product_id': product.product_ids.id,
                            'quantity': product.no_of_items,
                            'product': product.product_ids,
                            'product_combo_parent': product.product_tmpl_id.id
                        }
                        lines.append(line)
                # line = {
                #     'product_id': product_id.id,
                #     'price': line.price,
                #     'amount': line.amount,
                #     'uom': line.uom.id,
                #     'product_uom_category_id': line.product_uom_category_id.id,
                #     'quantity': line.quantity,
                #     'sale_online_id': line.sale_online_id.id,
                #     'product': product,
                # }
                # lines.append(line)
            partner = False
            if order.partner_id.id != False:
                partner_groups = []
                for group in order.partner_id.partner_groups:
                    partner_groups.append(group.id)
                partner = {
                    'id': order.partner_id.id,
                    'name': order.partner_id.name,
                    'street': order.partner_id.street,
                    'city': order.partner_id.city,
                    'state_id': False,
                    'country_id': False,
                    'vat': False,
                    'lang': False,
                    'phone': order.partner_id.phone,
                    'zip': False,
                    'mobile': False,
                    'email': order.partner_id.email,
                    'barcode': order.partner_id.barcode,
                    'write_date': order.partner_id.write_date,
                    'property_account_position_id': False,
                    'property_product_pricelist': False,
                    'loyalty_points': order.partner_id.loyalty_points,
                    'partner_groups': partner_groups,
                }
            _order = {
                'name': order.name,
                'date': order.date,
                'pos_config_id': order.pos_config_id.id,
                'price_list_id': order.price_list_id.id,
                'order_line_ids': lines,
                'customer': order.customer,
                'phone': order.phone,
                'address': order.address,
                'note': order.note,
                'partner': partner,
                'source_order_id': order.source_order_id.id
            }
            orders.append(_order)
        return orders

    def push_pos_order(self):
        message = []
        for record in self:
            if record.state == 'finish':
                return
            lines = []
            for line in record.order_line_ids:
                line = {
                    'product_id': line.product_id.id,
                    'price': line.price,
                    'amount': line.amount,
                    'uom': line.uom.id,
                    'product_uom_category_id': line.product_uom_category_id.id,
                    'quantity': line.quantity,
                    'sale_online_id': line.sale_online_id.id,
                }
                lines.append(line)
            order = {
                'name': record.name,
                'date': record.date,
                'pos_config_id': record.pos_config_id.id,
                'price_list_id': record.price_list_id.id,
                'order_line_ids': lines,
                'customer': record.customer,
                'phone': record.phone,
                'address': record.address,
                'note': record.note,
            }
            message = order
            self.description = _('Đơn hàng đã được đẩy đi')
            record.send_sync_message(message)

    def cancel_sale_online(self):
        for record in self:
            record.state = 'cancel'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code(
                    'sale.online') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.online') or _('New')
        result = super(SaleOnline, self).create(vals)
        return result

    def send_sync_message(self, message):
        self.ensure_one()
        channel_name = "pos.sale_online"
        self.env["pos.config"]._send_to_channel_by_id(self._cr.dbname, self.pos_config_id.id, channel_name, message)

    def unlink(self):
        for online_order in self.filtered(lambda online_order: online_order.state not in ['draft', 'cancel']):
            raise UserError(_('In order to delete a sale, it must be new or cancelled.'))
        return super(SaleOnline, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = _('New')
        default['state'] = 'draft'
        return super(SaleOnline, self).copy(default)

class PosOrderSaleOnline(models.Model):
    _inherit = "pos.order"

    sale_online = fields.Char('Ref Sale Online')
    note_sale_online = fields.Text(string='Internal Notes')

    @api.model
    def create_from_ui(self, orders, draft=False):
        for order in orders:
            date_order = order['data']['creation_date'].replace('T', ' ')[:19]
            date_order_zone7 = datetime.strptime(date_order, '%Y-%m-%d %H:%M:%S') + relativedelta(hours=7)

            date_order = date_order.split()
            now = datetime.now()
            date_now = now.strftime("%Y-%m-%d")
            if date_now != date_order[0]:
                raise UserError('Ngày máy tính cửa hàng đang khác so với ngày thực tế. Để tiếp tục hãy cấu hình lại ngày trên máy tính của bạn và load lại POS.')
            if 'pos_session_id' in order['data']:
                pos_session_id = self.env['pos.session'].search([('id','=', order['data']['pos_session_id'])])
                if pos_session_id.state != 'opened':
                    raise UserError('Phiên bán hàng đã bị đóng. Để tiếp tục bán hàng xin hãy mở lại phiên')
                # Check date order and session start differ (timezone GMT+7)
                start_at_zone7 = pos_session_id.start_at + relativedelta(hours=7)
                session_start_at = start_at_zone7.strftime("%Y-%m-%d")
                date_order_at = date_order_zone7.strftime("%Y-%m-%d")
                if date_order_at != session_start_at:
                    raise UserError('Bạn không thể bán hàng của phiên ngày hôm trước!')

        result = super(PosOrderSaleOnline, self).create_from_ui(orders, draft)
        for order in orders:
            if 'sale_online' in order['data'] and order['data']['sale_online'] != '':
                sale_online_id = self.env['sale.online'].search([('name', '=', order['data']['sale_online'])], limit=1)
                order_id = self._find_order_id(result, order['data']['name'])
                if sale_online_id.id != False:
                    if sale_online_id.state == 'sent':
                        sale_online_id.state = 'finish'
                if order_id != False:
                    sale_online_id.pos_order_id = order_id
        return result



    def _find_order_id(self, orders, key):
        for order in orders:
            if order['pos_reference'] == key:
                return order['id']
        return False

    @api.model
    def _order_fields(self, ui_order):
        result = super(PosOrderSaleOnline, self)._order_fields(ui_order)
        result['sale_online'] = ui_order.get('sale_online', '')
        result['note'] = ui_order.get('note', '')
        result['note_sale_online'] = ui_order.get('note_sale_online', '')
        return result


class PosConfigCheckOnline(models.Model):
    _inherit = 'pos.config'

    @api.model
    def check_online(self):
        return True

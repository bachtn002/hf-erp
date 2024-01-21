# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, except_orm
from odoo.osv import osv
from odoo.tools.float_utils import float_round
from dateutil.relativedelta import relativedelta


class ProductProcess(models.Model):
    _name = 'product.process'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # def _default_branch_id(self):
    #     branch_id = self.env['res.users'].browse(self._uid).branch_id.id
    #     return branch_id

    name = fields.Char("Name", default='/', copy=False)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')],
                             default='draft', track_visibility='onchange')
    note = fields.Text("Note", track_visibility='onchange')
    date = fields.Datetime("Date", default=fields.Datetime.now, track_visibility='onchange', copy=False, readonly=True)
    date_done = fields.Datetime("Date Done", track_visibility='onchange', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # branch_id = fields.Many2one('res.branch', default=_default_branch_id, required=True)
    location_id = fields.Many2one('stock.location', "Process at location", track_visibility='onchange')
    dest_location_id = fields.Many2one('stock.location', "Process to location", track_visibility='onchange')
    process_line_ids = fields.One2many('product.process.line', 'process_id', "Process lines")
    picking_ids = fields.Many2many('stock.picking', string='Picking', readonly=True, copy=False)
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    warehouse_id = fields.Many2one('stock.warehouse', string='Stock Warehouse', related='location_id.x_warehouse_id',
                                  readonly=True)

    @api.onchange('location_id')
    def _onchange_dest_location(self):
        for record in self:
            record.dest_location_id = record.location_id

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.process') or _('/')
        return super(ProductProcess, self).create(vals)

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError('Thông báo! Không thể xóa bản ghi ở trạng thái khác bản thảo')
        return super(ProductProcess, self).unlink()

    def _get_inventory(self, product_id, location_id, lot_id, qty):
        total_availability = self.env['stock.quant']._get_available_quantity(product_id, location_id, lot_id=lot_id)
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        total_availability = float_round(total_availability, precision_digits=precision_digits,
                                         rounding_method='HALF-UP')
        warehouse_id = self.location_id.get_warehouse()
        for record in warehouse_id:
            if not record.out_minus:
                if total_availability < qty:
                    raise ValidationError(_('Không đủ hàng! Sản phẩm "%s" không đủ hàng trong kho "%s-%s": %s') % (
                        product_id.name, location_id.name, location_id.name, total_availability))
        return qty

    def _check_lot_and_inventory(self):
        for line in self.process_line_ids:
            for detail in line.from_detail_ids:
                if detail.product_id.tracking != 'none' and not detail.lot_id:
                    raise ValidationError(_('Bạn chưa nhập mã lô cho sản phẩm "%s" ') % (detail.product_id.name))
                self._get_inventory(detail.product_id, self.location_id, detail.lot_id, detail.qty)
            for detail in line.to_detail_ids:
                if detail.product_id.tracking != 'none' and not detail.lot_id:
                    raise ValidationError(_('Bạn chưa nhập mã lô cho sản phẩm "%s" ') % (detail.product_id.name))

    def _check_qty(self):
        warehouse_id = self.location_id.get_warehouse()
        for line in self.process_line_ids:
            list_balance = []
            for detail in line.from_detail_ids:
                if warehouse_id.max_qty_process > 0:
                    if detail.qty > warehouse_id.max_qty_process:
                        raise UserError(_('Quantity than max quantity process'))
                # balance = detail.qty / detail.origin_qty
                # precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                # balance = float_round(balance, precision_digits=precision_digits, rounding_method='HALF-UP')
                # if balance not in list_balance:
                #     list_balance.append(balance)
            # if len(list_balance) != 1:
            #     raise ValidationError(_('Có sự chênh lệch bội số số lượng sản phẩm thao tác.'))
            # for detail in line.to_detail_ids:
            #     min_qty = list_balance[0] * detail.origin_qty * (100 - detail.error_percent) / 100
            #     max_qty = list_balance[0] * detail.origin_qty * (100 + detail.error_percent) / 100
            #     precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            #     min_qty = float_round(min_qty, precision_digits=precision_digits, rounding_method='HALF-UP')
            #     max_qty = float_round(max_qty, precision_digits=precision_digits, rounding_method='HALF-UP')
            #     detail.qty = float_round(detail.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
            #     if detail.qty < min_qty or detail.qty > max_qty:
            #         raise ValidationError(
            #             _('Có sự chênh lệch bội số số lượng sản phẩm "%s" được tạo thành. (Đã tính chênh lệch cho phép)') % (
            #                 detail.product_id.name))

    def _check_detail_process(self):
        for line in self.process_line_ids:
            line_id = self.env['product.process.line'].search([('process_id','=',self.id),('rule_id','=',line.rule_id.id)])
            if len(line_id) > 1:
                raise ValidationError(_('You are not allowed to process more than 1 part of the same rule!'))

    def action_back_to_draft(self):
        self.state = 'draft'

    def action_process(self):
        if self.state != 'draft':
            return True
        self.re_calculate_process_detail()
        self._check_lot_and_inventory()
        self._check_qty()
        self._check_detail_process()
        try:
            self.create_picking_out()
            self.create_picking_in()
        except Exception as e:
            raise UserError(_("Có vấn đề khi tạo đơn dịch chuyển kho: %s") % (e,))
        self.date = datetime.now()
        self.state = 'done'

    def _get_inventory_loss(self, product_id, location_id):
        # if not product_id.x_property_stock_manufactory_id:
        #     raise except_orm('Error!', 'Bạn phải cấu hình địa điểm ghi nhận chế biến cho sản phẩm "%s"' %product_id.name)
        # property_stock_inventory = product_id.x_property_stock_manufactory_id.id
        standard_price = product_id.standard_price
        warehouse_id = location_id.get_warehouse()
        property_stock_inventory = self.env['stock.warehouse'].search([('id', '=', warehouse_id.id)],
                                                                      limit=1).x_process_warehouse.id
        x_inventory_valuation_group_id = warehouse_id.x_inventory_valuation_group_id.id
        for product_price_id in product_id.product_price_ids:
            if x_inventory_valuation_group_id == product_price_id.inventory_valuation_group_id.id:
                standard_price = product_price_id.cost
        dict = {
            'property_stock_inventory': property_stock_inventory,
            'standard_price': standard_price
        }
        return dict

    def create_picking_out(self):
        StockPicking = self.env['stock.picking']
        PickingType = self.env['stock.picking.type']
        picking_type_id = PickingType.sudo().search(
            [('sequence_code', '=', 'OUT_OTHER'), ('company_id', '=', self.company_id.id)], limit=1)
        if not picking_type_id:
            raise ValidationError(
                _('Bạn chưa cấu hình kiểu giao nhân (IN_OTHER - OUT_OTHER) cho công ty "%s" ') % (self.company_id.name))
        property_stock_inventory_list = []
        move_lines = []
        for child_line in self.process_line_ids:
            move_lines = []
            amount = 0
            for line in child_line.from_detail_ids:
                amount += line.product_id.standard_price * line.qty
                product_vals = self._get_inventory_loss(line.product_id, self.location_id)
                property_stock_inventory = product_vals.get('property_stock_inventory')
                property_stock_inventory_list.append(property_stock_inventory)
                move_line_vals = {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.uom_id.id,
                    'qty_done': line.qty,
                    'location_id': self.location_id.id,
                    'location_dest_id': property_stock_inventory,
                    'date': fields.Datetime.now(),
                    'lot_id': line.lot_id.id if line.lot_id else False,
                    'lot_name': line.lot_id.name if line.lot_id else False,
                    'reference': self.name,
                    'state': 'assigned'
                }
                move_out_args = {
                    'reference': self.name,
                    'origin': self.name,
                    'note': self.note,
                    'picking_type_id': picking_type_id.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.qty,
                    'location_id': self.location_id.id,
                    'location_dest_id': property_stock_inventory,
                    # 'price_unit': self.product_id.standard_price * line.percent / 100,
                    'date': fields.Datetime.now(),
                    'state': 'assigned',
                    'move_line_ids': [(0, 0, move_line_vals)]
                }
                move_lines.append([0, 0, move_out_args])
            child_line.amount = amount
            warehouse_id = self.location_id.get_warehouse()
            picking_out_args = {
                'origin': self.name,
                'x_type_other': 'outgoing',
                'picking_type_id': picking_type_id.id,
                'move_lines': move_lines,
                'location_id': self.location_id.id,
                'location_dest_id': property_stock_inventory_list[0],
                'date': fields.Datetime.now(),
                'state': 'assigned',
                'x_analytic_account_id': warehouse_id.x_analytic_account_id.id if warehouse_id.x_analytic_account_id else None
            }
            picking_out = StockPicking.create(picking_out_args)
            picking_out._action_done()
            child_line.picking_out_id = picking_out.id
            for move in picking_out.move_lines:
                for move_line in move.move_line_ids:
                    move_line.picking_id = picking_out
            account_move = self.env['account.move'].search([('ref', '=', picking_out.name)])
            if account_move:
                for move in account_move:
                    move.ref = picking_out.name + ' - ' + self.name
            self.write({'picking_ids': [(4, picking_out.id)]})

    def create_picking_in(self):
        StockPicking = self.env['stock.picking']
        PickingType = self.env['stock.picking.type']
        picking_type_id = PickingType.search(
            [('sequence_code', '=', 'IN_OTHER'), ('company_id', '=', self.company_id.id)], limit=1)
        if not picking_type_id:
            raise ValidationError(
                _('Bạn chưa cấu hình kiểu giao nhân (IN_OTHER - OUT_OTHER) cho công ty "%s" ') % (self.company_id.name))
        property_stock_inventory_list = []
        for child_line in self.process_line_ids:
            move_lines = []
            amount = child_line.amount
            for line in child_line.to_detail_ids:
                product_vals = self._get_inventory_loss(line.product_id, self.location_id)
                property_stock_inventory = product_vals.get('property_stock_inventory')
                property_stock_inventory_list.append(property_stock_inventory)
                move_line_vals = {
                    'product_id': line.product_id.id,
                    'product_uom_id': line.uom_id.id,
                    'qty_done': line.qty,
                    'location_id': property_stock_inventory,
                    'location_dest_id': self.dest_location_id.id,
                    'date': fields.Datetime.now(),
                    'lot_id': line.lot_id.id if line.lot_id else False,
                    'lot_name': line.lot_id.name if line.lot_id else False,
                    'reference': self.name,
                    'state': 'assigned'
                }
                move_in_args = {
                    'reference': self.name,
                    'origin': self.name,
                    'note': self.note,
                    'picking_type_id': picking_type_id.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.qty,
                    'location_id': property_stock_inventory,
                    'location_dest_id': self.dest_location_id.id,
                    'price_unit': round(amount * line.percent / 100) / (line.qty),
                    'date': fields.Datetime.now(),
                    'state': 'assigned',
                    'move_line_ids': [(0, 0, move_line_vals)]
                }
                move_lines.append([0, 0, move_in_args])
            warehouse_id = self.dest_location_id.get_warehouse()
            picking_in_args = {
                'origin': self.name,
                'x_type_other': 'incoming',
                'picking_type_id': picking_type_id.id,
                'move_lines': move_lines,
                'location_id': property_stock_inventory_list[0],
                'location_dest_id': self.dest_location_id.id,
                'date': fields.Datetime.now(),
                'state': 'assigned',
                'x_analytic_account_id': warehouse_id.x_analytic_account_id.id if warehouse_id.x_analytic_account_id else None
            }
            picking_in = StockPicking.create(picking_in_args)
            picking_in._action_done()
            child_line.picking_in_id = picking_in.id
            for move in picking_in.move_lines:
                for move_line in move.move_line_ids:
                    move_line.picking_id = picking_in
            account_move = self.env['account.move'].search([('ref', '=', picking_in.name)])
            if account_move:
                for move in account_move:
                    move.ref = picking_in.name + ' - ' + self.name
            self.write({'picking_ids': [(4, picking_in.id)]})

    def action_cancel(self):
        try:
            self.ensure_one()
            if self.state == 'cancel':
                return
            stock_inventory = self.env['stock.inventory'].search([('x_location_id', '=', self.location_id.id)],
                                                                 order='date desc', limit=1)
            if stock_inventory:
                if self.date <= stock_inventory.date:
                    raise UserError(_('Inventory has been stocked you cannot cancel'))

            # fix lỗi singleton cancel congnd
            # self.picking_ids.action_cancel_picking()

            for picking in self.picking_ids:
                picking.action_cancel_picking()
            self.state = 'cancel'
        except Exception as e:
            raise ValidationError(e)

    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env["ir.actions.actions"].sudo()._for_xml_id("stock.action_picking_tree_all")

        pickings = self.mapped('picking_ids')
        action['domain'] = [('id', 'in', pickings.ids)]
        action['context'] = dict(self._context, create=0, delete=0, edit=0)
        return action

    def re_calculate_process_detail(self):
        try:
            for line in self.process_line_ids:
                balance = 1.0

                for from_process_id in line.from_detail_ids:
                    if from_process_id.qty != from_process_id.origin_qty:
                        balance = from_process_id.qty / from_process_id.origin_qty
                    if balance != 1:
                        break

                for from_process_id in line.from_detail_ids:
                    from_process_id.qty_change = from_process_id.qty

                for to_process_id in line.to_detail_ids:
                    to_process_id.qty = balance * to_process_id.origin_qty
        except Exception as e:
            raise ValidationError(e)

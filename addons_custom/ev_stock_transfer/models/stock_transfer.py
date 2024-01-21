# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, AccessError, except_orm
from odoo.osv import osv
import xlrd
import base64
import xlwt

try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
from datetime import datetime, timedelta


class StockTransfer(models.Model):
    _name = 'stock.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_warehouse(self):
        if self.env.user.has_group('ev_stock_access_right.group_stock_access_all'):
            warehouse_ids = self.env['stock.warehouse'].search([('active', '=', True)], limit=1)
        else:
            warehouse_ids = self.env.user.warehouse_ids
        for warehouse_id in warehouse_ids:
            warehouse = warehouse_id
        return warehouse.id

    name = fields.Char('Transfer Code', track_visibility='onchange', default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse', track_visibility='onchange',
                                   default=_default_warehouse)
    warehouse_name = fields.Char(string='Source warehouse name', related='warehouse_id.name')
    warehouse_dest_id = fields.Many2one('stock.warehouse', 'Destination Warehouse', track_visibility='onchange')
    warehouse_dest_name = fields.Char(string='Destination warehouse name', related='warehouse_dest_id.name')
    out_picking_id = fields.Many2one('stock.picking', 'Stock picking from')
    in_picking_id = fields.Many2one('stock.picking', 'Stock picking to')

    transfer_line_ids = fields.One2many('stock.transfer.line', 'stock_transfer_id', 'Operations',
                                        track_visibility='onchange')

    date = fields.Datetime(track_visibility='onchange', default=fields.Datetime.now)
    out_date = fields.Datetime('Out Date', track_visibility='onchange')
    in_date = fields.Datetime('In Date', track_visibility='onchange')
    origin = fields.Char('Source document', track_visibility='onchange')
    note = fields.Text('Note')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('ready', 'Ready'), ('transfer', 'Transfer'), ('done', 'Done'), ('cancel', 'Cancel')],
                             'State',
                             track_visibility='onchange', default="draft")
    out_transfer_count = fields.Integer(string='Out Transfer', compute='_compute_out_transfer')
    in_transfer_count = fields.Integer(string='In Transfer', compute='_compute_in_transfer')
    receiver = fields.Char('Receiver')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    total_quantity_out = fields.Float('Total quantity out', compute='_compute_total_out', track_visibility='onchange',
                                      digits='Product Unit of Measure')
    total_quantity_in = fields.Float('Total quantity in', compute='_compute_total_in', track_visibility='onchange')

    check_create = fields.Boolean(default=False)

    def _compute_total_out(self):
        for s in self:
            total_quantity_out = 0.0
            for line in s.transfer_line_ids:
                total_quantity_out += line.out_quantity
            s.total_quantity_out = total_quantity_out

    def _compute_total_in(self):
        for s in self:
            total_quantity_in = 0.0
            for line in s.transfer_line_ids:
                total_quantity_in += line.in_quantity
            s.total_quantity_in = total_quantity_in

    def _compute_out_transfer(self):
        for order in self:
            order.out_transfer_count = len(order.out_picking_id)

    def print_pick_products_template(self):
        # print single template
        # FIXME change to new template
        if self.state in ['draft', 'confirmed']:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_stock_transfer.report_template_stock_transfer_from/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            raise UserError(_('You can not print template when request state is not in draft or confirmed'))
        pass

    def action_print_transfer_pdf(self):
        if self.state == 'transfer' or self.state == 'done':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_stock_transfer.report_template_stock_transfer_internal_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            raise UserError(_('Inventory output no done!'))

    def action_print_transfer_to_pdf(self):
        if self.state == 'transfer' or self.state == 'done':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_stock_transfer.report_template_stock_transfer_to_internal_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            raise UserError(_('Inventory input no done!'))

    def do_print_bill_transfer_out(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_transfer.report_template_stock_picking_bill_transfer_out_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def do_print_bill_transfer_in(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_transfer.report_template_stock_picking_bill_transfer_in_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def action_view_out_transfer(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        # action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        if self.out_picking_id:
            action['domain'] = [('id', '=', self.out_picking_id.id)]
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = self.out_picking_id.id
        return action

    def _compute_in_transfer(self):
        for order in self:
            order.in_transfer_count = len(order.in_picking_id)

    def action_view_in_transfer(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        # action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        if self.in_picking_id:
            action['domain'] = [('id', '=', self.in_picking_id.id)]
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = self.in_picking_id.id
        return action

    def action_check_available(self):
        for record in self.warehouse_id:
            check_available = 0
            if not record.out_minus:
                for line in self.transfer_line_ids:
                    total_availability = self.env['stock.quant']._get_available_quantity(line.product_id,
                                                                                         self.out_picking_id.location_id)
                    precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                    total_availability = float_round(total_availability, precision_digits=precision_digits,
                                                     rounding_method='HALF-UP')
                    if total_availability >= line.quantity:
                        line.state = 'available'
                        line.available_qty = total_availability
                    else:
                        line.state = 'not_available'
                        line.available_qty = total_availability
                        check_available += 1
                if check_available == 0:
                    self.out_picking_id.action_confirm()
                    self.out_picking_id.action_assign()
                    self.state = 'ready'
            else:
                for line in self.transfer_line_ids:
                    total_availability = self.env['stock.quant']._get_available_quantity(line.product_id,
                                                                                         self.out_picking_id.location_id)
                    precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                    total_availability = float_round(total_availability, precision_digits=precision_digits,
                                                     rounding_method='HALF-UP')
                    line.available_qty = total_availability
                    line.state = 'available'
                self.out_picking_id.action_confirm()
                self.out_picking_id.action_assign()
                self.state = 'ready'

    def action_confirm(self):
        if self.state not in ('draft', 'not_available'):
            return True
        # if self.warehouse_dest_id.x_wh_transfer_loc_id.id == False:
        #     raise UserError(_("Chưa cấu hình địa điểm trung chuyển hàng hóa trong kho. Xin hãy liên hệ với người quản trị"))
        picking_type_from_id = self.warehouse_id.int_type_id
        dest_location_id = self.env['stock.location'].search(
            [('id', '=', self.warehouse_dest_id.x_location_transfer_id.id)],
            limit=1)
        if len(dest_location_id) == 0:
            raise UserError(
                _("Chưa cấu hình địa điểm trung chuyển hàng hóa trong kho. Xin hãy liên hệ với người quản trị"))
        if len(self.transfer_line_ids) == 0 and (
                self.out_picking_id.id == False or self.out_picking_id.state == 'cancel'):
            picking_id = self._create_picking_draft(picking_type_from_id.id, dest_location_id.id,
                                                    picking_type_from_id.default_location_src_id.id)
            if picking_id.id == False:
                raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
            self.update({'out_picking_id': picking_id.id})
        else:
            for line in self.transfer_line_ids:
                stock_transfer_line = self.env['stock.transfer.line'].search([('stock_transfer_id', '=', self.id),
                                                                              ('product_id', '=', line.product_id.id),
                                                                              ('qty_available', '=', 'True')], limit=1)
                if stock_transfer_line and len(self.transfer_line_ids) > 1:
                    stock_transfer_line.quantity += line.quantity
                    sql = """
                        Delete from stock_transfer_line a
                        where id = %d;
                    """
                    self._cr.execute(sql % (line.id))
                    self._cr.commit()
                else:
                    line.qty_available = 'True'
            if self.out_picking_id.id == False or self.out_picking_id.state == 'cancel':
                picking_id = self._create_picking(picking_type_from_id.id, dest_location_id.id,
                                                  picking_type_from_id.default_location_src_id.id)
                if picking_id:
                    self.update({'out_picking_id': picking_id.id})
                else:
                    raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))

        self.out_picking_id.x_type_transfer = 'out_transfer'
        self.state = 'confirmed'

    def _create_picking_draft(self, picking_type_id, location_dest_id, location_id, check_transfer=True):
        StockPicking = self.env['stock.picking']
        for transfer in self:
            res = transfer._prepare_picking(picking_type_id, location_dest_id, location_id)
            picking = StockPicking.create(res)
            picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': picking, 'origin': transfer},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return picking

    def _create_picking(self, picking_type_id, location_dest_id, location_id, check_transfer=True):
        StockPicking = self.env['stock.picking']
        picking = False
        for transfer in self:
            if any([ptype in ['product', 'consu'] for ptype in transfer.transfer_line_ids.mapped('product_id.type')]):
                res = transfer._prepare_picking(picking_type_id, location_dest_id, location_id)
                picking = StockPicking.create(res)
                moves = transfer.transfer_line_ids._create_stock_moves(picking, check_transfer)
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': transfer},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return picking

    @api.model
    def _prepare_picking(self, picking_type_id, location_dest_id, location_id):
        return {
            'picking_type_id': picking_type_id,
            'date': self.date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id
        }

    def action_transfer(self, picking):
        location_id = self.env['stock.location'].search([('id', '=', self.warehouse_dest_id.x_location_transfer_id.id)],
                                                        limit=1)
        if len(location_id) == 0:
            raise UserError(
                _("Chưa cấu hình địa điểm trung chuyển hàng hóa trong kho. Xin hãy liên hệ với người quản trị"))
        if picking == True:
            if not self.in_picking_id:
                picking_type_to_id = self.warehouse_dest_id.sudo().int_type_id
                picking_id = self._create_picking(picking_type_to_id.id, picking_type_to_id.default_location_dest_id.id,
                                                  location_id.id, False)
                if picking_id.id == False:
                    raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
                self.update({'in_picking_id': picking_id.id})
                self.in_picking_id.action_confirm()
                self.in_picking_id.action_assign()
            for line in self.transfer_line_ids:
                line.state = 'available'
            self.state = 'transfer'
        else:
            check_backorder = False
            check_qty = False
            for record in self.transfer_line_ids:
                if record.out_quantity != 0:
                    check_qty = True
                    break
            if not check_qty:
                for line in self.transfer_line_ids:
                    stock_move = self.env['stock.move'].search([('x_out_transfer_line_id', '=', line.id)], limit=1)
                    if stock_move:
                        for move_line in stock_move.move_line_ids:
                            move_line.picking_id = self.out_picking_id.id
                            if line.out_quantity > 0:
                                move_line.qty_done = line.out_quantity
                                check_backorder = True
                            else:
                                move_line.qty_done = line.quantity
                                line.out_quantity = line.quantity
            else:
                for line in self.transfer_line_ids:
                    stock_move = self.env['stock.move'].search([('x_out_transfer_line_id', '=', line.id)], limit=1)
                    if stock_move:
                        for move_line in stock_move.move_line_ids:
                            move_line.picking_id = self.out_picking_id.id
                            if line.out_quantity > 0:
                                move_line.qty_done = line.out_quantity
                                check_backorder = True
            self.out_picking_id.button_validate()
            if not self.in_picking_id:
                picking_type_to_id = self.warehouse_dest_id.sudo().int_type_id
                picking_id = self._create_picking(picking_type_to_id.id, picking_type_to_id.default_location_dest_id.id,
                                                  location_id.id, False)
                if picking_id.id == False:
                    raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
                self.update({'in_picking_id': picking_id.id})
                self.in_picking_id.action_confirm()
                self.in_picking_id.action_assign()
            if self.out_picking_id.state == 'done':
                self.state = 'transfer'
            else:
                if check_backorder == True:
                    args_backorder = {
                        'pick_ids': [(6, 0, self.out_picking_id.ids)]
                    }
                    backorder_id = self.env['stock.backorder.confirmation'].create(args_backorder)
                    backorder_id.process_cancel_backorder()
                self.state = 'transfer'
        if self.in_picking_id:
            self.in_picking_id.x_type_transfer = 'in_transfer'
            self.in_picking_id.action_assign()
        self.out_date = datetime.now()

    def action_receive(self):
        if self.state != 'transfer':
            return False
        check_backorder = False
        for line in self.transfer_line_ids:
            stock_move = self.env['stock.move'].search([('x_in_transfer_line_id', '=', line.id)], limit=1)
            if stock_move:
                for move_line in stock_move.move_line_ids:
                    move_line.picking_id = self.in_picking_id.id
                    if line.in_quantity > 0:
                        move_line.qty_done = line.in_quantity
                        check_backorder = True
                    else:
                        move_line.qty_done = line.out_quantity
                        line.in_quantity = line.out_quantity
        self.in_picking_id.button_validate()
        if self.in_picking_id.state == 'done':
            self.state = self.in_picking_id.state
        else:
            if check_backorder == True:
                args_backorder = {
                    'pick_ids': [(6, 0, self.in_picking_id.ids)]
                }
                backorder_id = self.env['stock.backorder.confirmation'].create(args_backorder)
                backorder_id.process_cancel_backorder()
            self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer') or _('New')
        if "transfer_line_ids" in vals.keys():
            product_list = []
            for obj in vals['transfer_line_ids']:
                if obj[2]['product_id'] not in product_list:
                    product_list.append(obj[2]['product_id'])
            list_new = vals['transfer_line_ids']
            new_list = []
            for obj in product_list:
                count = 0
                qty = 0
                for element in list_new:
                    if obj == element[2]['product_id']:
                        qty += element[2]['quantity']
                for ele in list_new:
                    if obj == ele[2]['product_id']:
                        count += 1
                        if count == 1:
                            ele[2]['quantity'] = qty
                            new_list.append(ele)
            vals['transfer_line_ids'] = new_list
        return super(StockTransfer, self).create(vals)

    def unlink(self):
        if self.state == 'draft':
            if self.check_create:
                raise UserError(_('Thông báo! Bạn không thể xóa phiếu điểu chuyển này'))
            else:
                return super(StockTransfer, self).unlink()
        raise UserError(_('Thông báo! Bạn chỉ có thể xóa ở trạng thái nháp'))

    def action_back(self):
        if self.out_picking_id:
            self.out_picking_id.action_cancel()
            self.out_picking_id.unlink()
        for line in self.transfer_line_ids:
            line.qty_available = ''
        self.state = 'draft'

    def action_set_draft(self):
        if self.out_picking_id:
            self.out_picking_id.unlink()
        self.state = 'draft'

    def action_cancel(self):
        if self.state == 'draft':
            self.state = 'cancel'

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def action_import_line(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                product_code = str(int(product_code)).upper()
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                qty = sheet.cell(index, 3).value
                note = sheet.cell(index, 4).value
                if product_id:
                    line_obj = self.env['stock.transfer.line'].search(
                        [('stock_transfer_id', '=', self.id), ('product_id', '=', product_id.id)], limit=1)
                    if line_obj:
                        line_obj.quantity += qty
                    else:
                        move_vals = {
                            'product_id': product_id.id,
                            'name': product_id.name,
                            'product_uom': product_id.product_tmpl_id.uom_id.id,
                            'quantity': qty,
                            'stock_transfer_id': self.id,
                            'note': note
                        }
                        line_id = self.env['stock.transfer.line'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!", (e))

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_stock_transfer/static/template/import_ev_stock_transfer.xlsx',
            "target": "_parent",
        }

    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_transfer.report_template_stock_picking_internal_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def action_choose_out_date(self):
        for record in self.transfer_line_ids:
            for line in self.out_picking_id.move_ids_without_package:
                if line.product_id.id == record.product_id.id:
                    line.quantity_done = record.out_quantity
        self.out_date = datetime.now()
        self.action_transfer(False)

    def auto_fill_out_quantity(self):
        for line in self.transfer_line_ids:
            line.out_quantity = line.quantity

    def action_choose_in_date(self):
        warehouse = self.env['stock.warehouse'].search([('id', '=', self.warehouse_dest_id.id)])
        self.in_date = datetime.now()
        self.action_receive()

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_stock_transfer.stock_transfer_xlsx/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def sort_product(self):
        temp = []
        sort_product = []
        for i in self:
            for v in i.transfer_line_ids:
                temp.append(v.product_id.product_tmpl_id.categ_id.name)

                temp.append(v.product_id.default_code)

                temp.append(v.product_id.name)

                temp.append(v.product_uom.name)

                temp.append(v.out_quantity)

                temp.append(v.product_id.product_tmpl_id.x_product_code_id.id)

                sort_product.append(list(temp))
                temp.clear()
            for k in range(0, len(sort_product) - 1):
                for m in range(k + 1, len(sort_product)):
                    if sort_product[k][2] > sort_product[m][2]:
                        temp = sort_product[k]
                        sort_product[k] = sort_product[m]
                        sort_product[m] = temp
        return sort_product

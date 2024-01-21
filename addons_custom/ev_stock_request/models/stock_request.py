# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv
import xlrd
import base64
from datetime import date
from datetime import datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockRequest(models.Model):
    _name = 'stock.request'
    _order = 'date_request ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Stock Request'

    name = fields.Char('Number', default=lambda self: _('New'))
    date_request = fields.Date('Date', default=lambda x: datetime.today(), track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse', string='Source warehouse', track_visibility='onchange')
    warehouse_name = fields.Char(string='Source warehouse name', related='warehouse_id.name')
    warehouse_dest_id = fields.Many2one('stock.warehouse', string='Destination warehouse',
                                        track_visibility='onchange',
                                        domain=[('x_is_supply_warehouse', '!=', None)])
    warehouse_dest_name = fields.Char(string='Destination warehouse name', related='warehouse_dest_id.name')

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          track_visibility='onchange')

    @api.onchange('warehouse_dest_id')
    def onchange_warehouse_dest(self):
        self.analytic_account_id = self.warehouse_dest_id.x_analytic_account_id.id

    type = fields.Selection(
        [('transfer', 'Transfer'), ('other_input', 'Other Input'), ('other_output', 'Other Output')],
        default='transfer')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], copy=False, default='draft', track_visibility='onchange')
    note = fields.Text('Note', track_visibility='onchange')
    stock_transfer_id = fields.Many2one('stock.transfer', string='Transfer', track_visibility='onchange')
    stock_picking_id = fields.Many2one('stock.picking', string='Other Transfer', track_visibility='onchange')
    location_id = fields.Many2one('stock.location', string='Reason', track_visibility='onchange')
    valuation_in_account_id = fields.Many2one('account.account', 'Stock Counterpart Account (Incoming)')
    valuation_out_account_id = fields.Many2one('account.account', 'Stock Counterpart Account (Outgoing)')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    line_ids = fields.One2many('stock.request.line', 'request_id', string='Information')

    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    transfer_count = fields.Integer(string='Transfer Out', compute='_compute_transfer')
    picking_count = fields.Integer(string='Picking', compute='_compute_picking')
    picking_count_in = fields.Integer(string='Picking In', compute='_compute_picking')
    stock_request_imp_name = fields.Char(string='Stock Request IMP Name')

    account_expense_item = fields.Many2one('account.expense.item', string='Account Expense Item')


    @api.onchange('location_id')
    def onchange_location_id(self):
        try:
            if self.location_id:
                location_id = self.env['stock.location'].sudo().search([('id', '=', self.location_id.id)], limit=1)
                if location_id:
                    self.account_expense_item = location_id.x_account_expense_item
                    self.valuation_in_account_id = location_id.valuation_in_account_id
                    self.valuation_out_account_id = location_id.valuation_out_account_id
        except Exception as e:
            raise ValidationError(e)

    def _compute_transfer(self):
        for order in self:
            order.transfer_count = len(order.stock_transfer_id)

    def _compute_picking(self):
        for order in self:
            order.picking_count = len(order.stock_picking_id)
            order.picking_count_in = order.picking_count

    def action_view_transfer(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('ev_stock_transfer.action_stock_transfer_from').sudo().read()[0]

        if self.stock_transfer_id:
            action['domain'] = [('id', '=', self.stock_transfer_id.id)]
            action['views'] = [(self.env.ref('ev_stock_transfer.stock_transfer_from_form_view').id, 'form')]
            action['res_id'] = self.stock_transfer_id.id
        return action

    def action_view_picking(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        if self.type == 'other_input':
            action = self.env.ref('ev_stock_other.action_stock_picking_incoming_other').sudo().read()[0]
        elif self.type == 'other_output':
            action = self.env.ref('ev_stock_other.action_stock_picking_outgoing_other').sudo().read()[0]

        if self.stock_picking_id:
            action['domain'] = [('id', '=', self.stock_picking_id.id)]
            action['views'] = [(self.env.ref('ev_stock_other.stock_view_picking_other_form').id, 'form')]
            action['res_id'] = self.stock_picking_id.id
        return action

    def action_send(self):
        self.ensure_one()
        if self.state != 'draft':
            return True
        if not self.line_ids:
            raise ValidationError(_("Missing products required!!"))
        for line in self.line_ids:
            if line.qty <= 0:
                raise ValidationError(_("The number of requests must be greater than 0!!"))
            else:
                uom_qty = float_round(line.qty, precision_rounding=line.uom_id.rounding, rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                              defined on the unit of measure "%s". Please change the quantity done or the \
                                                              rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.uom_id.name))
            if self.type == 'other_input' and not line.price_unit:
                raise ValidationError(_("Bạn cần nhập đơn giá Nhập Khác!"))
        if self.type == 'transfer':
            if self.warehouse_id.id == self.warehouse_dest_id.id:
                raise ValidationError(_("Please choose 2 different warehouses"))
            self.state = 'to_approve'
        else:
            PickingType = self.env['stock.picking.type']
            if self.type == 'other_input':
                picking_type_id = PickingType.search(
                    [('sequence_code', '=', 'IN_OTHER'), ('company_id', '=', self.env.company.id)], limit=1).id
                location_id = self.location_id.id
                location_dest_id = self.warehouse_dest_id.lot_stock_id.id
                x_type_other = 'incoming'
            else:
                picking_type_id = PickingType.search(
                    [('sequence_code', '=', 'OUT_OTHER'), ('company_id', '=', self.env.company.id)], limit=1).id
                location_id = self.warehouse_dest_id.lot_stock_id.id
                location_dest_id = self.location_id.id
                x_type_other = 'outgoing'
            picking_id = self._create_picking(picking_type_id, location_dest_id, location_id, x_type_other, True)
            self.set_note_picking_in_out_comming(picking_id)
            self.stock_picking_id = picking_id
            if self.location_id.x_account_expense_item:
                self.stock_picking_id.x_account_expense_item = self.location_id.x_account_expense_item
            if self.type == 'other_input':
                self.stock_picking_id.action_confirm()
            if self.type == 'other_output':
                self.stock_picking_id.action_confirm()
                self.stock_picking_id.action_assign()
            self.state = 'done'
        stock_request_imp_line = self.env['stock.request.import.line'].search([('stock_request_id', '=', self.id)])
        stock_request_imp = self.env['stock.request.import'].search(
            [('id', '=', stock_request_imp_line.stock_request_import_id.id)])
        if stock_request_imp_line:
            for record in stock_request_imp_line:
                for line in self.line_ids:
                    if record.product_id.id == line.product_id.id:
                        if stock_request_imp.type == 'other_input':
                            record.state = 'assigned'
                        elif self.type == 'other_output':
                            record.status = 'draft_picking'

    def action_approve(self):
        self.ensure_one()
        if self.state != 'to_approve':
           return
        check_qty = False
        for line in self.line_ids:
            if line.qty_apply != 0:
                check_qty = True
        if not check_qty:
            for line in self.line_ids:
                if line.qty_apply == 0:
                    line.qty_apply = line.qty
        for line in self.line_ids:
            if line.qty_apply <= 0:
                raise ValidationError(_("The number of requests must be greater than 0!!"))
            else:
                uom_qty = float_round(line.qty_apply, precision_rounding=line.uom_id.rounding,
                                      rounding_method='HALF-UP')
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                qty = float_round(line.qty_apply, precision_digits=precision_digits, rounding_method='HALF-UP')
                if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                    raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                                     defined on the unit of measure "%s". Please change the quantity done or the \
                                                                     rounding precision of your unit of measure.') % (
                        line.product_id.display_name, line.uom_id.name))
        if self.company_id.x_auto_create_transfer == True:
            self.create_stock_transfer()
            self.state = 'done'
        else:
            self.state = 'approve'

    def action_auto_fill(self):
        check_qty = False
        for line in self.line_ids:
            if line.qty_apply != 0:
                check_qty = True
        if not check_qty:
            for line in self.line_ids:
                if line.qty_apply == 0:
                    line.qty_apply = line.qty

    def action_cancel_approve(self):
        self.ensure_one()
        if self.state == 'cancel':
            return True

    def action_reject(self):
        self.ensure_one()
        if self.state != 'to_approve':
            return True
        self.state = 'reject'

    def action_back(self):
        self.ensure_one()
        if self.state == 'to_approve':
            self.state = 'draft'

    def action_transfer(self):
        self.ensure_one()
        if self.state == 'done':
            return
        if all([x.qty_apply <= 0 for x in self.line_ids]):
            raise UserError(_("Please insert quantity for confirm"))
        self.create_stock_transfer()
        self.state = 'done'

    def create_stock_transfer(self):
        transfer_obj = self.env['stock.transfer']
        transfer_line_obj = self.env['stock.transfer.line']
        vals = {
            'warehouse_id': self.warehouse_dest_id.id,
            'warehouse_dest_id': self.warehouse_id.id,
            'origin': self.name,
            'state': 'draft',
            'note': self.note,
            'check_create': True
        }
        transfer_id = transfer_obj.create(vals)
        for line in self.line_ids:
            if line.qty_apply > 0:
                vals_line = {
                    'stock_transfer_id': transfer_id.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'quantity': line.qty_apply,
                    'note': line.note
                }
                transfer_line_obj.create(vals_line)
            self.stock_transfer_id = transfer_id.id

    def _create_picking(self, picking_type_id, location_dest_id, location_id, x_type_other, check_transfer=True):
        StockPicking = self.env['stock.picking']
        picking = False
        for transfer in self:
            if any([ptype in ['product', 'consu'] for ptype in transfer.line_ids.mapped('product_id.type')]):
                res = transfer._prepare_picking(picking_type_id, location_dest_id, location_id, x_type_other)
                picking = StockPicking.create(res)
                moves = transfer.line_ids._create_stock_moves(picking, check_transfer)
        return picking

    def _prepare_picking(self, picking_type_id, location_dest_id, location_id, x_type_other):
        return {
            'picking_type_id': picking_type_id,
            'date': self.date_request,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id,
            'x_type_other': x_type_other,
            'x_analytic_account_id': self.analytic_account_id.id if self.analytic_account_id else None
        }

    def action_cancel(self):
        if self.state == 'done':
            if self.stock_transfer_id.state == 'draft':
                self.state = 'cancel'
                self.stock_transfer_id.action_cancel()
            else:
                raise UserError(_("Phiểu chuyển kho đang ở trạng thái khác nháp, bạn không thể hủy được!'."))
                return True

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_("You cannot delete record if the state is not 'Draft'."))
        return super(StockRequest, self).unlink()

    @api.model
    def create(self, vals):
        res = super().create(vals)
        # send mail activity
        # create name when create record
        month = date.today().month
        year = date.today().year
        day = date.today().day
        # Format prefix: RQ%(y)s%(month)s/xxxx
        prefix = f'STR{year % 100}{month:02d}{day:02d}/'
        request_id = self.env['stock.request'].search([('company_id', '=', res.company_id.id), ('id', '!=', res.id)],
                                                      order='create_date desc', limit=1)
        if not request_id:
            res.name = f'{prefix}000001'
        else:
            number = int(request_id.name.split('/')[1])
            suffix = f'{number + 1:06d}'
            res.name = f'{prefix}{suffix}'
        # end
        return res

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default['stock_transfer_id'] = False
        default['stock_picking_id'] = False
        res = super(StockRequest, self).copy(default)
        for line in self.line_ids:
            line.copy({'request_id': res.id})
        return res

    def _create_send_notification(self):
        res_notification_obj = self.env['res.notification'].sudo()
        vals_list = []
        self = self.sudo()
        dest_warehouse_users = self.dest_warehouse_id.user_ids
        warehouse_users = self.warehouse_id.user_ids
        users = dest_warehouse_users | warehouse_users
        msg = 'Phiếu yêu cầu: {} được tạo bởi {}'.format(self.name, self.create_uid.name)
        for user_id in users:
            vals = {
                'type': 'web',
                'message': msg,
                'user_id': user_id.id,
                'state': 'draft',
                'company_id': self.env.company.id,
                'model': 'stock.request',
                'item_id': self.id,
            }
            vals_list.append(vals)
        if vals_list:
            # create record in res_notification
            notification_ids = res_notification_obj.create(vals_list)
            for notification in notification_ids:
                notification.action_send_message()

    def _done_message(self):
        ResNotification = self.env['res.notification'].sudo()
        res_notification_ids = ResNotification.search([('model', '=', 'stock.request'), ('item_id', '=', self.id)])
        for res_notification_id in res_notification_ids:
            res_notification_id.action_done_web()

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.lower().endswith('.xls') is False and file_name.lower().endswith('.xlsx') is False:
            return False
        return True

    def _is_number(self, name):
        try:
            float(name)
            return True
        except ValueError:
            return False

    def action_import_line(self):
        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.field_binary_import))
        except:
            raise UserError(_("File not found or in incorrect format. Please check the .xls or .xlsx file format"))
        try:
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            check_product = []
            check_price = []
            check_qty = []
            lines = []
            for i in range(3, sheet.nrows):
                default_code = str(sheet.cell_value(i, 1)).split('.')[0]
                product_id = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
                if not product_id or not product_id.active:
                    check_product.append(i + 1)
                if self.type == 'other_input':
                    if float(sheet.cell_value(i, 4)):
                        if float(sheet.cell_value(i, 4)) <= 0:
                            check_price.append(i + 1)
                    else:
                        check_price.append(i + 1)
                if float(sheet.cell_value(i, 5)):
                    if float(sheet.cell_value(i, 5)) <= 0:
                        check_qty.append(i + 1)
                else:
                    check_qty.append(i + 1)
            product_error = ' , '.join([str(elem) for elem in check_product])
            price_error = ' , '.join([str(price) for price in check_price])
            qty_error = ' , '.join([str(qty) for qty in check_qty])
            mess_error = ''
            if check_product:
                mess_error += _('\nProduct does not exist in the system, line (%s)') % str(product_error)
            if check_qty:
                mess_error += _('\nQuantity must be greater than 0, line (%s)') % str(qty_error)
            if self.type == 'other_input':
                if check_price:
                    mess_error += _('\nPrice must be greater than 0, line (%s)') % str(price_error)
            if mess_error:
                raise UserError(mess_error)
            else:
                for i in range(3, sheet.nrows):
                    default_code = str(sheet.cell_value(i, 1)).split('.')[0]
                    product_id = self.env['product.product'].search([('default_code', '=', default_code)],
                                                                    limit=1)
                    price = sheet.cell_value(i, 4)
                    if self.type == 'other_input':
                        price = float(sheet.cell_value(i, 4))
                    for record in self:
                        check = False
                        if record.line_ids:
                            for rec in record.line_ids:
                                if rec.product_id.id == product_id.id:
                                    rec.qty += float(sheet.cell_value(i, 5))
                                    check = True
                        if not check:
                            argvs_request = (0, 0, {
                                'request_id': record.id,
                                'product_id': product_id.id,
                                'uom_id': product_id.product_tmpl_id.uom_id.id,
                                'price_unit': price,
                                'qty': float(sheet.cell_value(i, 5)),
                                'note': sheet.cell_value(i, 6),
                            })
                            lines.append(argvs_request)

            self.line_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None

        except Exception as e:
            raise ValidationError(e)

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_stock_request/static/template/import_stock_request.xlsx',
            "target": "_parent",
        }

    def _action_unlink_activity(self):
        for activity_id in self.activity_ids:
            activity_id.with_user(activity_id.user_id).unlink()

    @api.onchange('type')
    def onchange_picking_type_depend_x_type(self):
        if self.type:
            if self.type == 'other_input':
                return {
                    'domain': {
                        'location_id': [('x_is_reason', '=', True), ('x_type_other', '=', 'incoming'),
                                        ('usage', '=', 'inventory'), '|',
                                        ('company_id', '=', self.company_id.id),
                                        ('company_id', '=', False)]
                    }
                }
            elif self.type == 'other_output':
                return {
                    'domain': {
                        'location_id': [('x_is_reason', '=', True), ('x_type_other', '=', 'outgoing'),
                                        ('usage', '=', 'inventory'), '|',
                                        ('company_id', '=', self.company_id.id),
                                        ('company_id', '=', False)]
                    }
                }

    def button_cancel(self):
        self.stock_transfer_id.action_cancel()
        self.state = 'cancel'

    def set_note_picking_in_out_comming(self, picking):
        try:
            for line in self.line_ids:
                for line_move in picking.move_ids_without_package:
                    if line.product_id.id == line_move.product_id.id:
                        line_move.x_note_in_out_comming = line.note
        except Exception as e:
            raise ValidationError(e)

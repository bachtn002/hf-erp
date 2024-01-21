# -*- coding: utf-8 -*-
import base64
import datetime
from odoo import models, fields, api, _

import xlrd

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockRequestImp(models.Model):
    _name = 'stock.request.import'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    date = fields.Date('Date', default=lambda x: fields.Date.today())
    type = fields.Selection([('other_input', 'Other Input'), ('other_output', 'Other Output')], default='other_input')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], copy=False, default='draft', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    note = fields.Text('Note')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    line_ids = fields.One2many('stock.request.import.line', 'stock_request_import_id', 'Stock Request Import Line')
    picking_count = fields.Float(compute='_compute_picking_count', default=0)

    def action_set_draft(self):
        try:
            self.ensure_one()
            if self.state == 'draft':
                return
            elif self.state == 'confirmed':
                for line in self.line_ids:
                    if line.stock_request_id and line.stock_request_id.state != 'done':
                        line.stock_request_id.unlink()
                self.state ='draft'
        except Exception as e:
            raise ValidationError(e)

    def unlink(self):
        if self.state != 'draft':
            raise UserError(_("You cannot delete record if the state is not 'Draft'."))
        return super(StockRequestImp, self).unlink()

    def action_stock_picking(self):
        self.ensure_one()
        stock_picking_ids = []
        for line in self.line_ids:
            if line.stock_request_id:
                picking_id = self.env['stock.picking'].search([('origin', '=', line.stock_request_id.name)]).id
                if picking_id:
                    stock_picking_ids.append(picking_id)
        line_ids = list(set(stock_picking_ids))
        action = self.env['ir.actions.act_window']._for_xml_id('ev_stock_other.action_stock_picking_incoming_other')
        action['context'] = {}
        action['domain'] = [('id', 'in', line_ids)]
        return action

    @api.depends('line_ids', 'line_ids.stock_request_id')
    def _compute_picking_count(self):
        for record in self:
            stock_request_ids = []
            record.picking_count = 0
            if record.line_ids:
                for line in record.line_ids:
                    if line.stock_request_id:
                        stock_request_ids.append(line.stock_request_id.id)
            request_ids = self.env['stock.request'].search([('id', 'in', stock_request_ids)])
            if request_ids:
                for rec in request_ids:
                    if rec.picking_count:
                        if rec.picking_count:
                            record.picking_count += rec.picking_count

    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            date = self.date.strftime('%d/%m/%Y')
            self.name = 'Import Nhập/Xuất khác ngày' + str(date)

    def action_send(self):
        self.ensure_one()
        if self.state == 'done':
            return
        for line in self.line_ids:
            if line.stock_request_id:
                if line.stock_request_id.state == 'draft':
                    for qty_line in line.stock_request_id.line_ids:
                        print(qty_line.price_unit)
                    line.stock_request_id.action_send()
        self.state = 'done'
        if self.type == 'other_input':
            for line in self.line_ids:
                line.state = 'assigned'
        elif self.type == 'other_output':
            for line in self.line_ids:
                line.status = 'draft_picking'

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'confirmed':
            return
        self._generate_request()
        self.state = 'confirmed'
        if self.type == 'other_input':
            for line in self.line_ids:
                line.state = 'confirmed'
        elif self.type == 'other_output':
            for line in self.line_ids:
                line.status = 'confirmed'

    def _generate_request(self):
        for line in self.line_ids:
            stock_request_line_imp = self.env['stock.request.import.line'].search(
                [('stock_request_import_id', '=', self.id), ('warehouse_dest_id', '=', line.warehouse_dest_id.id),
                 ('location_id', '=', line.location_id.id), ('stock_request_id', '!=', False),
                 ('analytic_account_id', '=', line.analytic_account_id.id)])
            if stock_request_line_imp:
                self.env['stock.request.line'].create({
                    'request_id': stock_request_line_imp.stock_request_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'qty': line.quantity,
                    'note': line.note,
                    'price_unit': line.price_unit
                })
                line.stock_request_id = stock_request_line_imp.stock_request_id.id
            else:
                pos_shop_id = self.env['pos.shop'].sudo().search([('warehouse_id', '=', line.warehouse_dest_id.id)],
                                                                 limit=1)
                stock_request_id = self.env['stock.request'].create({
                    'date_request': self.date,
                    'type': self.type,
                    'stock_request_imp_name': self.name,
                    'state': 'draft',
                    'note': self.note,
                    'company_id': self.company_id.id,
                    'warehouse_dest_id': line.warehouse_dest_id.id,
                    'location_id': line.location_id.id,
                    'valuation_in_account_id': line.valuation_in_account_id.id if line.valuation_in_account_id else None,
                    'valuation_out_account_id': line.valuation_out_account_id.id if line.valuation_out_account_id else None,
                    'account_expense_item': line.account_expense_item.id if line.account_expense_item else None,
                    'analytic_account_id': line.analytic_account_id.id
                })
                self.env.cr.commit()
                self.env['stock.request.line'].create({
                    'request_id': stock_request_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'qty': line.quantity,
                    'note': line.note,
                    'price_unit': line.price_unit
                })
                self.env.cr.commit()
                line.stock_request_id = stock_request_id.id

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_stock_request/static/template/import_many_stock_request.xlsx',
            "target": "_parent",
        }

    def action_import_line(self):
        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.field_binary_import))
        except:
            raise ValidationError(_('Import file must be an excel file'))
        try:
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            check_warehouse_dest = []
            check_location = []
            check_reason = []
            check_product = []
            check_qty = []
            check_price_unit = []
            check_analytic_account = []
            for i in range(1, sheet.nrows):
                warehouse_dest_id = self.env['stock.warehouse'].search([('code', '=', sheet.cell_value(i, 0))], limit=1)
                if not warehouse_dest_id:
                    check_warehouse_dest.append(i + 1)
                location_id = self.env['stock.location'].search(
                    [('x_code', '=', sheet.cell_value(i, 1)), ('usage', '=', 'inventory')], limit=1)
                if not location_id:
                    check_location.append(i + 1)
                if location_id.x_type_other == 'incoming' and self.type == 'other_output':
                    check_reason.append(i + 1)
                if location_id.x_type_other == 'outgoing' and self.type == 'other_input':
                    check_reason.append(i + 1)
                default_code = str(sheet.cell_value(i, 2)).split('.')[0]
                product_id = self.env['product.product'].search([('default_code', '=', default_code)])
                analytic_account_code = sheet.cell_value(i, 5)
                analytic_account = self.env['account.analytic.account'].search(
                        [('code', '=', analytic_account_code)], limit=1)
                if not analytic_account:
                    check_analytic_account.append(i + 1)
                if not product_id:
                    check_product.append(i + 1)
                if float(sheet.cell_value(i, 3)) <= 0:
                    check_qty.append(i + 1)
                if self.type == 'other_input':
                    if sheet.cell_value(i, 4) != '':
                        if float(sheet.cell_value(i, 4)) <= 0:
                            check_price_unit.append(i + 1)
                    else:
                        check_price_unit.append(i + 1)

            warehouse_dest_error = ' , '.join([str(warehouse) for warehouse in check_warehouse_dest])
            location_error = ' , '.join([str(location) for location in check_location])
            reason_error = ' , '.join([str(reason) for reason in check_reason])
            product_error = ' , '.join([str(product) for product in check_product])
            qty_error = ' , '.join([str(qty) for qty in check_qty])
            price_unit_error = ' , '.join([str(price_unit) for price_unit in check_price_unit])
            analytic_account_error = ' , '.join([str(analytic_account) for analytic_account in check_analytic_account])
            mess_error = ''
            if check_warehouse_dest:
                mess_error += _('\nWarehouse dest does not exist in the system, line (%s)') % str(warehouse_dest_error)
            if check_location:
                mess_error += _('\nReason does not exist in the system, line (%s)') % str(location_error)
            if check_reason:
                mess_error += _('\nReason is different from the type stock other, line (%s)') % str(reason_error)
            if check_product:
                mess_error += _('\nProduct does not exist in the system, line (%s)') % str(product_error)
            if check_qty:
                mess_error += _('\nQuantity must be greater than 0, line (%s)') % str(qty_error)
            if check_price_unit:
                mess_error += _('\nPrice Unit must be greater than 0, line (%s)') % str(price_unit_error)
            if check_analytic_account:
                mess_error += _('\nAnalytic account does not exist in the system, line (%s)') % str(
                    analytic_account_error)

            if mess_error:
                raise UserError(mess_error)
            else:
                for i in range(1, sheet.nrows):
                    quantity = float(sheet.cell_value(i, 3))
                    price_unit = sheet.cell_value(i, 4)
                    if self.type == 'other_input':
                        price_unit = float(sheet.cell_value(i, 4))
                    analytic_account_code = sheet.cell_value(i, 5)
                    note = sheet.cell_value(i, 6)
                    default_code = str(sheet.cell_value(i, 2)).split('.')[0]
                    warehouse_dest_id = self.env['stock.warehouse'].search([('code', '=', sheet.cell_value(i, 0))],
                                                                           limit=1)
                    analytic_account_id = self.env['account.analytic.account'].search(
                        [('code', '=', analytic_account_code)], limit=1)
                    location_id = self.env['stock.location'].search(
                        [('x_code', '=', sheet.cell_value(i, 1)), ('usage', '=', 'inventory')], limit=1)
                    product_id = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
                    stock_request_import_line = self.env['stock.request.import.line'].search(
                        [('stock_request_import_id', '=', self.id), ('product_id', '=', product_id.id),
                         ('location_id', '=', location_id.id),
                         ('warehouse_dest_id', '=', warehouse_dest_id.id),
                         ('analytic_account_id', '=', analytic_account_id.id)], limit=1)
                    if stock_request_import_line:
                        stock_request_import_line.quantity = quantity
                    else:
                        state = 'draft'
                        if self.type == 'other_input':
                            self.env['stock.request.import.line'].create({
                                'stock_request_import_id': self.id,
                                'product_id': product_id.id,
                                'warehouse_dest_id': warehouse_dest_id.id,
                                'location_id': location_id.id,
                                'valuation_in_account_id': location_id.valuation_in_account_id.id if location_id.valuation_in_account_id else None,
                                'valuation_out_account_id': location_id.valuation_out_account_id.id if location_id.valuation_out_account_id else None,
                                'account_expense_item': location_id.x_account_expense_item.id if location_id.x_account_expense_item else None,
                                'quantity': quantity,
                                'note': note,
                                'price_unit': price_unit,
                                'uom_id': product_id.uom_id.id,
                                'state': state,
                                'analytic_account_id': analytic_account_id.id,
                            })
                            self.env.cr.commit()
                        elif self.type == 'other_output':
                            self.env['stock.request.import.line'].create({
                                'stock_request_import_id': self.id,
                                'product_id': product_id.id,
                                'warehouse_dest_id': warehouse_dest_id.id,
                                'location_id': location_id.id,
                                'valuation_in_account_id': location_id.valuation_in_account_id.id if location_id.valuation_in_account_id else None,
                                'valuation_out_account_id': location_id.valuation_out_account_id.id if location_id.valuation_out_account_id else None,
                                'account_expense_item': location_id.x_account_expense_item.id if location_id.x_account_expense_item else None,
                                'quantity': quantity,
                                'note': note,
                                'price_unit': price_unit,
                                'uom_id': product_id.uom_id.id,
                                'status': state,
                                'analytic_account_id': analytic_account_id.id,
                            })
                            self.env.cr.commit()

            self.field_binary_import = None
            self.field_binary_name = None
        except Exception as e:
            raise ValidationError(e)


class StockRequestIMP(models.Model):
    _name = 'stock.request.import.line'

    stock_request_import_id = fields.Many2one(comodel_name='stock.request.import', string='Stock Request Import',
                                              ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure')
    warehouse_dest_id = fields.Many2one('stock.warehouse', string='Destination warehouse')
    location_id = fields.Many2one('stock.location', string='Reason')
    note = fields.Text('Note')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    stock_request_id = fields.Many2one('stock.request', 'Request')
    price_unit = fields.Float('Price Unit')
    quantity_done = fields.Float('Quantity Done', digits='Product Unit of Measure', readonly=True)
    valuation_in_account_id = fields.Many2one('account.account', 'Stock Counterpart Account (Incoming)')
    valuation_out_account_id = fields.Many2one('account.account', 'Stock Counterpart Account (Outgoing)')
    account_expense_item = fields.Many2one('account.expense.item', string='Account Expense Item')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('done', 'Done'),
    ], string="State Picking In", copy=False, readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('draft_picking', 'Draft Picking'),
        ('wait', 'Wait'),
        ('assigned', 'Assigned'),
        ('done', 'Done'),
    ], string="State Picking Out", copy=False, readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id

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

    @api.onchange('warehouse_dest_id')
    def onchange_warehouse_dest_id(self):
        self.analytic_account_id = False
        if self.warehouse_dest_id:
            self.analytic_account_id = self.warehouse_dest_id.x_analytic_account_id.id
# -*- coding: utf-8 -*-
from odoo import models, fields, api

try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
from odoo.osv import osv
import xlrd
import base64
from odoo.exceptions import UserError, AccessError, except_orm


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_type_other = fields.Selection([('incoming', 'Incoming'), ('outgoing', 'Outgoing')], copy=True,
                                    string="Type Other")
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    x_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                            track_visibility='onchange')
    x_check_other_input = fields.Boolean(default=False, compute='_compute_check_other_input')

    x_warehouse_location_name = fields.Char(string='Warehouse Location Out', related='location_id.x_warehouse_id.name')
    x_warehouse_location_dest_name = fields.Char(string='Warehouse Location In', related='location_dest_id.x_warehouse_id.name')

    @api.depends('origin')
    def _compute_check_other_input(self):
        for record in self:
            record.x_check_other_input = False
            if record.origin:
                stock_request = self.env['stock.request'].search([('name', '=', record.origin)], limit=1)
                if stock_request:
                    for rec in stock_request:
                        if rec.type != 'transfer':
                            record.x_check_other_input = True

    def _action_done(self):
        if self.x_type_other == 'incoming':
            for move in self.move_lines:
                move.name = move.product_id.default_code + '-' + move.product_id.name + '-' + self.location_dest_id.name + '-' + self.name
        if self.x_type_other == 'outgoing':
            for move in self.move_lines:
                move.name = move.product_id.default_code + '-' + move.product_id.name + '-' + self.location_id.name + '-' + self.name
        super(StockPicking, self)._action_done()

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
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                if type(product_code).__name__ == 'str':
                    product_code = product_code.upper()
                else:
                    product_code = str(int(product_code)).upper()
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code)))
                qty = sheet.cell(index, 3).value
                note = sheet.cell(index, 4).value
                if product_id:
                    line_obj = self.env['stock.move'].search(
                        [('picking_id', '=', self.id), ('product_id', '=', product_id.id)], limit=1)
                    if line_obj:
                        line_obj.product_uom_qty += qty
                    else:
                        move_vals = {
                            'name': self.name or '',
                            'product_id': product_id.id,
                            'product_uom': product_id.product_tmpl_id.uom_id.id,
                            'product_uom_qty': qty,
                            'date': self.scheduled_date,
                            'date_expected': self.scheduled_date,
                            'location_id': self.location_id.id,
                            'location_dest_id': self.location_dest_id.id,
                            'picking_id': self.id,
                            'state': 'draft',
                            'company_id': self.company_id.id,
                            'picking_type_id': self.picking_type_id.id,
                            'route_ids': (self.picking_type_id.warehouse_id and [
                                (6, 0, [x.id for x in self.picking_type_id.warehouse_id.route_ids])] or []),
                            'warehouse_id': self.picking_type_id.warehouse_id.id,
                        }
                        line_id = self.env['stock.move'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_stock_other/static/template/import_ev_stock_other.xlsx',
            "target": "_parent",
        }

    @api.onchange('picking_type_id')
    def onchange_picking_type_depend_x_type(self):
        if not self.picking_type_id.id:
            context = self._context
            PickingType = self.env['stock.picking.type']
            if 'default_x_type_other' in context.keys():
                if context.get('default_x_type_other') == 'incoming':
                    self.picking_type_id = PickingType.search([('sequence_code', '=', 'IN_OTHER'), ('company_id', '=', self.env.company.id)],
                                                              limit=1).id
                    return {
                        'domain': {
                            'location_id': [('x_is_reason', '=', True), ('x_type_other', '=', 'incoming'),
                                            ('usage', '=', 'inventory'), '|',
                                            ('company_id', '=', self.company_id.id),
                                            ('company_id', '=', False)],
                            'location_dest_id': [('usage', '=', 'internal'), '|',
                                                 ('company_id', '=', self.company_id.id),
                                                 ('company_id', '=', False)],
                        }
                    }
                elif context.get('default_x_type_other') == 'outgoing':
                    self.picking_type_id = PickingType.search([('sequence_code', '=', 'OUT_OTHER'), ('company_id', '=', self.env.company.id)],
                                                              limit=1).id

                    return {
                        'domain': {
                            'location_dest_id': [('x_is_reason', '=', True), ('x_type_other', '=', 'outgoing'),
                                                 ('usage', '=', 'inventory'), '|',
                                                 ('company_id', '=', self.company_id.id),
                                                 ('company_id', '=', False)],
                            'location_id': [('usage', '=', 'internal'), '|',
                                            ('company_id', '=', self.company_id.id),
                                            ('company_id', '=', False)],
                        }
                    }

    def action_print_other(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_other.report_template_stock_picking_other_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }


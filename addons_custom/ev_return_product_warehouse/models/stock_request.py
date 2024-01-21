# -*- coding: utf-8 -*-

import xlrd3
import base64

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockRequest(models.Model):
    _inherit = 'stock.request'

    is_return_product = fields.Boolean('Is return goods to the warehouse')

    @api.onchange('warehouse_id', 'warehouse_dest_id')
    def _onchange_warehouse_id(self):
        # self.warehouse_dest_id = False
        try:
            if self.is_return_product:
                ids = []

                if not self.warehouse_id:
                    return {'domain': {'warehouse_dest_id': [('id', 'in', ids)]}}
                query = """
                    select warehouse_id
                    from general_warehouse_group
                    where id in (
                        SELECT group_id
                        from list_warehouse_group_general
                        WHERE warehouse_id = %s
                    )
                    order by warehouse_id
                """ % (self.warehouse_id.id)
                self._cr.execute(query)
                warehouse_ids = self._cr.fetchall()
                for id in warehouse_ids:
                    if id[0] not in ids:
                        ids.append(id[0])
                # if len(ids) > 0:
                #     self.warehouse_dest_id = ids[0]
                return {'domain': {'warehouse_dest_id': [('x_is_supply_warehouse', '=', True), ('id', 'in', ids)]}}

        except Exception as e:
            raise ValidationError(e)

    def _check_product_in_warehouse(self):
        try:
            pos_shop = self.env['pos.shop'].sudo().search([('warehouse_id', '=', self.warehouse_id.id)])
            product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', pos_shop.product_ids.ids)])

            list_product_errors = []

            for line in self.line_ids:
                if not self.warehouse_id.x_is_supply_warehouse:
                    if not line.product_id.product_tmpl_id.active:
                        list_product_errors.append(line.product_id.product_tmpl_id.name)
                        continue
                    if not line.product_id.product_tmpl_id.x_is_tools:
                        if line.product_id in product_ids:
                            if not line.product_id.product_tmpl_id.sale_ok:
                                list_product_errors.append(line.product_id.product_tmpl_id.name)
                            elif not line.product_id.product_tmpl_id.available_in_pos and line.product_id.product_tmpl_id.sale_ok:
                                list_product_errors.append(line.product_id.product_tmpl_id.name)
                        else:
                            list_product_errors.append(line.product_id.product_tmpl_id.name)

            mess_error = ' , '.join([str(err) for err in list_product_errors])
            if len(mess_error) != 0:
                raise UserError(_('Product can not send request : (%s)') % str(mess_error))
        except Exception as e:
            raise ValidationError(e)

    def action_transfer_return(self):
        self.ensure_one()
        if self.state == 'done':
            return
        self._check_product_in_warehouse()
        if all([x.qty_apply <= 0 for x in self.line_ids]):
            raise UserError(_("Please insert quantity for confirm"))
        for line in self.line_ids:
            uom_qty = float_round(line.qty_apply, precision_rounding=line.uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty = float_round(line.qty_apply, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                                                          defined on the unit of measure "%s". Please change the quantity done or the \
                                                                          rounding precision of your unit of measure.') % (
                    line.product_id.display_name, line.uom_id.name))
        self.create_stock_transfer_return()
        self.state = 'done'

    def create_stock_transfer_return(self):
        transfer_obj = self.env['stock.transfer']
        transfer_line_obj = self.env['stock.transfer.line']
        vals = {
            'warehouse_id': self.warehouse_id.id,
            'warehouse_dest_id': self.warehouse_dest_id.id,
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

    def action_import_return(self):
        try:
            wb = xlrd3.open_workbook(file_contents=base64.decodestring(self.field_binary_import))
        except:
            raise UserError(_("File not found or in incorrect format. Please check the .xls or .xlsx file format"))
        try:
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            check_product = []
            check_price = []
            check_qty = []
            lines = []
            check_type = []
            for i in range(3, sheet.nrows):
                default_code = str(sheet.cell_value(i, 1)).split('.')[0]
                pos_shop = self.env['pos.shop'].sudo().search(
                    [('warehouse_id', '=', self.warehouse_id.id)])
                product_id = self.env['product.product'].search(
                    [('default_code', '=', default_code), ('active', '=', True)], limit=1)
                if not product_id:
                    check_product.append(i + 1)
                else:
                    if not self.warehouse_id.x_is_supply_warehouse:
                        if not product_id.product_tmpl_id.x_is_tools:
                            if product_id.product_tmpl_id in pos_shop.product_ids:
                                if not product_id.product_tmpl_id.available_in_pos and product_id.product_tmpl_id.sale_ok:
                                    check_product.append(i + 1)
                            else:
                                check_product.append(i + 1)
                    if product_id.product_tmpl_id.type == 'service':
                        check_type.append(i + 1)
                if float(sheet.cell_value(i, 5)):
                    if float(sheet.cell_value(i, 5)) <= 0:
                        check_qty.append(i + 1)
                else:
                    check_qty.append(i + 1)
            product_error = ' , '.join([str(elem) for elem in check_product])
            price_error = ' , '.join([str(price) for price in check_price])
            qty_error = ' , '.join([str(qty) for qty in check_qty])
            type_error = ' , '.join([str(pr_type) for pr_type in check_type])
            mess_error = ''
            if check_product:
                mess_error += _('\nProduct does not exist in warehouse, line (%s)') % str(product_error)
            if check_qty:
                mess_error += _('\nQuantity must be greater than 0, line (%s)') % str(qty_error)
            if check_type:
                mess_error += _('\nNot service type, line (%s)') % str(type_error)

            if mess_error:
                raise UserError(mess_error)
            else:
                for i in range(3, sheet.nrows):
                    default_code = str(sheet.cell_value(i, 1)).split('.')[0]
                    product_id = self.env['product.product'].search([('default_code', '=', default_code)],
                                                                    limit=1)
                    for record in self:
                        check = False
                        if record.line_ids:
                            for rec in record.line_ids:
                                if rec.product_id.id == product_id.id:
                                    rec.qty_apply += float(sheet.cell_value(i, 5))
                                    check = True
                        if not check:
                            argvs_request = (0, 0, {
                                'request_id': record.id,
                                'product_id': product_id.id,
                                'uom_id': product_id.product_tmpl_id.uom_id.id,
                                'qty_apply': float(sheet.cell_value(i, 5)),
                                'note': sheet.cell_value(i, 6),
                            })
                            lines.append(argvs_request)

            self.line_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None

        except Exception as e:
            raise ValidationError(e)

# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.osv import osv
import xlrd
import base64
from odoo.exceptions import UserError, AccessError,except_orm


class PurchaseUtilities(models.Model):
    _inherit = 'purchase.order'

    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    x_total_quantity = fields.Float('Total Quantity', compute='_compute_total_quantity')
    
    def button_open_wizard_import_po_line_by_excel(self):
        self.ensure_one()
        return {
            'name': _(''),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.purchase.order.line',
            'no_destroy': True,
            'target': 'new',
            'view_id': self.env.ref('ev_purchase_utilities.wizard_import_purchase_order_line_view_form') and self.env.ref('ev_purchase_utilities.wizard_import_purchase_order_line_view_form').id or False,
            'context': {'default_order_id': self.id},
        }

    def _compute_total_quantity(self):
        for s in self:
            total_quantity = 0.0
            for line in s.order_line:
                total_quantity += line.product_qty
            s.x_total_quantity = total_quantity

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
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
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_code = str(product_code).replace('.0', '')
                if self._is_number(product_code):
                    product_code = str(int(product_code)).upper()
                else:
                    product_code = str(product_code).upper()
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_obj:
                    raise except_orm('Cảnh báo!',
                                     ("Mã sản phẩm không đúng. Vui lòng kiểm tra lại dòng " + str(
                                         index + 1) + 'của đơn hàng'))
                else:
                    product_id = product_obj[0]
                quantity = sheet.cell(index, 1).value
                price_unit = sheet.cell(index, 2).value
                tax = sheet.cell(index, 3).value
                tax_id = self.env['account.tax'].search([('amount','=', tax),('type_tax_use','=','purchase'),('company_id','=',self.company_id.id)], limit = 1)
                if tax_id:
                    tax_id = tax_id.id
                else:
                    tax_id = None
                argvs = {
                    'product_id': product_id.id,
                    'product_uom': product_id.product_tmpl_id.uom_id.id,
                    'product_qty': quantity,
                    'price_unit': price_unit,
                    'name': product_id.name,
                    'date_planned' : self.date_planned,
                    'order_id': self.id,
                    'taxes_id': [(6, 0, [tax_id])],
                }
                self.env['purchase.order.line'].create(argvs)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def action_clear_line(self):
        if self.order_line:
            self.order_line.unlink()

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_purchase_utilities/static/template/purchase_order_import.xlsx',
            "target": "_parent",
        }




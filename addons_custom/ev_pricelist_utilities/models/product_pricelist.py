# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError, except_orm
from odoo.osv import osv
from dateutil.relativedelta import relativedelta
import xlrd3
import base64
from datetime import datetime


class ProductPriceList(models.Model):
    _inherit = 'product.pricelist'

    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if not file_name.lower().endswith('.xls') and not file_name.lower().endswith('.xlsx'):
            return False
        return True

    def action_import_line(self):
        if self.field_binary_name is None:
            raise ValidationError('Không tìm thấy file import. Vui lòng chọn lại file import.')
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise ValidationError(
                    "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx")
            data = base64.decodebytes(self.field_binary_import)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 3
            product_pricelist_item_obj = self.env['product.pricelist.item']
            while index < sheet.nrows:
                product_code = str(sheet.cell(index, 0).value)
                product_obj = self.env['product.template'].search(
                    [('default_code', '=', product_code)], limit=1)

                start_date = sheet.cell(index, 4).value
                end_date = sheet.cell(index, 5).value
                qty = sheet.cell(index, 2).value
                if start_date:
                    date_time = datetime.fromordinal(
                        datetime(1900, 1, 1).toordinal() + int(start_date) - 2)
                    start_date = datetime.strftime(date_time - relativedelta(hours=7), '%Y-%m-%d %H:%M:%S')
                if end_date:
                    date_time = datetime.fromordinal(
                        datetime(1900, 1, 1).toordinal() + int(end_date) - 2)
                    end_date = datetime.strftime(date_time - relativedelta(hours=7), '%Y-%m-%d %H:%M:%S')
                if not product_obj:
                    raise ValidationError('Không tìm thấy SP có mã %s tại dòng %s' % (product_code, index + 1))
                price = sheet.cell(index, 3).value
                pricelist_item_id = product_pricelist_item_obj.search(
                    [('product_tmpl_id', '=', product_obj.id), ('pricelist_id', '=', self.id)], limit=1)
                if not pricelist_item_id:
                    argvs = {
                        'pricelist_id': self.id,
                        'applied_on': '1_product',
                        'product_tmpl_id': product_obj.id,
                        'min_quantity': float(qty),
                        'compute_price': 'fixed',
                        'fixed_price': price,
                        'date_start': start_date if start_date else None,
                        'date_end': end_date if end_date else None,
                        # 'base_pricelist_id':3,
                        # 'price_surcharge': price_surcharge,
                    }
                    product_pricelist_item_obj.create(argvs)
                else:
                    pricelist_item_id.fixed_price = price
                    pricelist_item_id.min_quantity = float(qty)
                    if start_date:
                        pricelist_item_id.date_start = start_date
                    if end_date:
                        pricelist_item_id.date_end = end_date
                    # pricelist_item_id.price_surcharge = price_surcharge
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except Exception as e:
            raise ValidationError(e)

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pricelist_utilities/static/template/import_price_list.xlsx',
            "target": "self",
        }

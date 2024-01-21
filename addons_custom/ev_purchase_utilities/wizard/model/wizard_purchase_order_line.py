# -*- coding: utf-8 -*-

import base64
import re
import tempfile
from datetime import datetime, date

import xlsxwriter

from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import xlrd


class WizardImportPurchaseOrderLine(models.TransientModel):
    _name = 'wizard.import.purchase.order.line'
    _inherits = {'ir.attachment': 'attachment_id'}

    import_date = fields.Date(required=False, default=date.today(), string='Import Date')
    template_file_url_default = fields.Char(default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
        'web.base.url') + '/ev_purchase_utilities/static/imp_donmuahang.xlsx',
                                            string='Template File URL')
    order_id = fields.Many2one('purchase.order')
    error_message = fields.Text()

    def action_button_ok(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    def action_import_po_line(self):
        self.ensure_one()
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/imp_donmuahang_' + user.login + '_' + str(self[0].id) + '_' + str(
            datetime.now()).replace(":",'_') + '.xlsx'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)
        if len(excel_data[0]) < 4:
            raise ValidationError(_('File excel phải có ít nhất 4 cột '))
        excel_data = excel_data[6:]
        row_number = 7
        dict_error = dict()
        date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for row in excel_data:
            value = {'order_id': self.order_id.id, 'company_id': self.order_id.company_id.id}
            space = len('Row{}: '.format(row_number)) + 8
            if not row[0]:
                dict_error.update({row_number: _('- Bạn cần nhập mã sản phẩm\n') + ' ' * space})
            else:
                product = self.env['product.product'].search([('default_code', '=', str(row[0]).strip())])
                if product.id:
                    if row[1]:
                        name = str(row[1])
                    else:
                        name = '[{}] {}'.format(product.default_code, product.name)
                    value.update({'product_id': product[0].id, 'name': name, 'product_uom': product.uom_id.id})
                else:
                    dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(' Không thể tìm thấy sản phẩm với mã {} trong hệ thống\n').format(
                        row[0]) + ' ' * space})

            if row[3]:
                try:
                    row[3] = str(row[3]).replace(',', '.')
                    f = float(row[3])
                    if f <= 0:
                        dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(
                            ' Số lượng đặt hàng phải lớn hơn 0\n') + ' ' * space})
                    else:
                        value.update({'product_qty': f})
                except:
                    dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(
                        ' Số lượng đặt hàng sai định dạng\n') + ' ' * space})
            else:
                dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(
                    ' Bạn cần nhập số lượng đặt hàng\n') + ' ' * space})

            if row[4]:
                try:
                    row[4] = str(row[4]).replace(',', '.')
                    g = float(row[4])
                    if g <= 0:
                        dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(
                            ' Đơn giá phải lớn hơn 0\n') + ' ' * space})
                    else:
                        value.update({'price_unit': g})
                except:
                    dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(
                        ' Đơn giá sai định dạng\n') + ' ' * space})
            else:
                dict_error.update({row_number: dict_error.get(row_number, '') + '-' + _(
                    ' Bạn cần nhập đơn giá\n') + ' ' * space})

            if row_number not in dict_error:
                product = self.env['product.product'].browse(value.get('product_id'))
                product_uom_ids = self.env['uom.uom'].search([('category_id', '=', product.uom_id.category_id.id)]).ids
                if value.get('product_uom', False) not in product_uom_ids:
                    dict_error.update({row_number: dict_error.get('row_number', '') + '-' + _(
                        ' Đơn vị tính được chọn không cùng loại với đơn vị tính trong sản phẩm') + ' ' * space})
                else:
                    price_unit = product_qty = 0
                    value.update({'date_planned': date_planned})
                    fpos = self.order_id.fiscal_position_id
                    if self.env.uid == SUPERUSER_ID:
                        value.update({'company_id': self.env.user.company_id.id})
                        if self.order_id.company_id.currency_id.id == self.order_id.currency_id.id:
                            value.update({'taxes_id': [(6, False, fpos.map_tax(product.supplier_taxes_id.filtered(lambda r: r.company_id.id == value.get('company_id'))).ids)]})
                    else:
                        if self.order_id.company_id.currency_id.id == self.order_id.currency_id.id:
                            value.update({'taxes_id': [(6, False, fpos.map_tax(product.supplier_taxes_id).ids)]})
                    params = {'order_id': self.order_id}

                    seller = product._select_seller(
                        partner_id=self.order_id.partner_id,
                        quantity=product_qty,
                        date=self.order_id.date_order and self.order_id.date_order.date(),
                        # uom_id=self.env['product.product'].browse(value.get('product_uom', False)).product_uom,
                        uom_id=self.env['uom.uom'].browse(value['product_uom']),
                        params=params)
                    if seller or not date_planned:
                        value.update({'date_planned': self.env['purchase.order.line']._get_date_planned(
                            seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                    company = self.env['res.company'].browse(value['company_id'])
                    product_uom = self.env['uom.uom'].browse(value.get('product_uom', False))
                    if not seller:
                        if product.seller_ids.filtered(lambda s: s.name.id == self.order_id.partner_id.id):
                            price_unit = 0.0
                    else:
                        if self.order_id.company_id.currency_id.id == self.order_id.currency_id.id:
                            taxes = self.env['account.tax'].browse(value.get('taxes_id', False)[0][2])
                            company = self.env['res.company'].browse(value['company_id'])
                            price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                                 product.supplier_taxes_id,
                                                                                                 taxes,
                                                                                                 company) if seller else 0.0
                        else:
                            price_unit = seller.price
                        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
                            price_unit = seller.currency_id._convert(
                                price_unit, self.order_id.currency_id, self.order_id.company_id,
                                self.order_id.date_order or fields.Date.today())
                        product_uom = self.env['uom.uom'].browse(value.get('product_uom', False))
                        if seller and product_uom and seller.product_uom != product_uom:
                            price_unit = seller.product_uom._compute_price(price_unit, product_uom)
                        value.update({'date_planned': date_planned})
                    if not value.get('price_unit'):
                        value.update({'price_unit': price_unit})
                    order_line = self.env['purchase.order.line'].create(value)
            row_number += 1
        if dict_error:
            # fileobj_or_path = tempfile.gettempdir() + path
            # wb = xlsxwriter.Workbook(fileobj_or_path)
            # ws = wb.add_worksheet()
            # table_header = wb.add_format({
            #     'bold': 1,
            #     'text_wrap': True,
            #     'align': 'center',
            #     'valign': 'vcenter',
            #     'border': 1,
            #     'font_name': 'Times New Roman',
            #     'font_size': 11,
            # })
            # table_header_error = wb.add_format({
            #     'bold': 1,
            #     'text_wrap': True,
            #     'align': 'center',
            #     'valign': 'vcenter',
            #     'border': 1,
            #     'font_name': 'Times New Roman',
            #     'font_size': 11,
            #     'bg_color': '#FFC7CE'
            # })
            # row_default_left = wb.add_format({
            #     'text_wrap': True,
            #     'align': 'left',
            #     'valign': 'vcenter',
            #     'font_name': 'Times New Roman',
            #     'border': 1,
            #     'font_size': 11,
            # })
            # row_default_left_error = wb.add_format({
            #     'text_wrap': True,
            #     'align': 'left',
            #     'valign': 'vcenter',
            #     'font_name': 'Times New Roman',
            #     'border': 1,
            #     'font_size': 11,
            #     'bg_color': '#FFC7CE'
            # })
            # ws.set_column('A:A', 15)
            # ws.set_column('B:B', 15)
            # ws.set_column('C:C', 15)
            # ws.set_column('D:D', 100)
            # ws.write('A1', 'Mã sản phẩm', table_header)
            # ws.write('B1', 'Miêu tả', table_header)
            # ws.write('C1', 'Số lượng', table_header)
            # ws.write('D1', 'Chi tiết lỗi', table_header_error)
            # row = 7
            message = ''
            for i in dict_error:
                 message += 'Hàng {} : {}'.format(i, dict_error[i]) + '\n'
            #     ws.write('A{}'.format(row), excel_data[(i - 2)][0], row_default_left)
            #     ws.write('B{}'.format(row), excel_data[(i - 2)][1], row_default_left)
            #     ws.write('C{}'.format(row), excel_data[(i - 2)][2], row_default_left)
            #     ws.write('D{}'.format(row), re.sub(' +', ' ', dict_error[i].replace('\n', '')).replace(' -', ','),
            #              row_default_left_error)
            #     row += 1
            # wb.close()
            self.write({'error_message': _(message)})
            # f = open(fileobj_or_path, "rb")
            # data = f.read()
            # xlsx_data = base64.b64encode(data)
            # self.attachment_id.write({
            #     'datas': xlsx_data,
            #     # 'datas_fname': 'Error_' + self.datas_fname
            # })
            return {
                'name': _('Warning'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wizard.import.purchase.order.line',
                'no_destroy': True,
                'res_id': self.id,
                'target': 'new',
                'view_id': self.env.ref(
                    'ev_purchase_utilities.wizard_import_purchase_order_line_view_form_warning') and self.env.ref(
                    'ev_purchase_utilities.wizard_import_purchase_order_line_view_form_warning').id or False,
            }

    def is_date(self, s):
        try:
            if isinstance(s,str):
                return False
            return True
        except ValueError:
            return True

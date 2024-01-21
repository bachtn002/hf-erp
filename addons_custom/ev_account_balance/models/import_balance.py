# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, except_orm
from odoo.osv import osv
import xlrd
import base64


class ImportAccountBalance(models.TransientModel):
    _name = 'account.balance.transient'

    file_upload = fields.Binary(string='File upload')
    file_name = fields.Char(string='File name')

    def action_import_data(self):
        try:
            data = base64.decodestring(self.file_upload)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            Branch = self.env['res.branch']
            Partner = self.env['res.partner']
            Account = self.env['account.account']
            Blance = self.env['account.balance']
            Product = self.env['product.product']
            while index < sheet.nrows:
                name = sheet.cell(index, 0).value
                branch_code = sheet.cell(index, 1).value
                partner_code = sheet.cell(index, 2).value
                account_code = sheet.cell(index, 3).value
                credit = sheet.cell(index, 4).value
                debit = sheet.cell(index, 5).value
                product_code = sheet.cell(index, 7).value
                qty = sheet.cell(index, 8).value or 0.0
                date_date = '2020-04-30'
                lot_line = []
                branch_id = Branch.sudo().search([('code', '=', branch_code),('company_id','=',1)], limit=1)
                if branch_id.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại chi nhánh có mã " + str(
                                         branch_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                account_id = Account.sudo().search([('code', '=', account_code),('company_id','=',1)], limit=1)
                if account_id.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại tài khoản có mã " + str(
                                         account_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                partner_id = False
                if partner_code:
                    partner_id = Partner.sudo().search(['|',('x_partner_code', '=', partner_code),('x_partner_old_code','=', partner_code)], limit=1)
                    if partner_id.id == False:
                        raise except_orm('Cảnh báo!',
                                         ("Không tồn tại đối tác có mã " + str(
                                             partner_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                             index + 1)))
                    partner_id = partner_id.id
                product_id = False
                if product_code:
                    product_id = Product.sudo().search([('default_code', '=', product_code)], limit=1)
                    if product_id.id == False:
                        raise except_orm('Cảnh báo!',
                                         ("Không tồn tại SP có mã " + str(
                                             product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                             index + 1)))
                    product_id = product_id.id
                Blance.create({
                    'name': name,
                    'account_id': account_id.id,
                    'debit': debit if type(debit) == float else 0,
                    'credit': credit if type(credit) == float else 0,
                    'date': date_date,
                    'company_id': 1,
                    'branch_id': branch_id.id,
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'qty': qty,
                })
                index = index + 1
            self.file_upload = None
            self.file_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

# -*- coding: utf-8 -*-
import base64
import datetime

import xlrd
import pytz

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class AccountStatementIMP(models.TransientModel):
    _name = 'account.statement.import.line'

    account_statement_file = fields.Binary(string='Choose File')

    def import_account_statement_xlrd(self):
        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.account_statement_file))
        except:
            raise ValidationError(_('Import file must be an excel file'))
        try:
            data = base64.decodebytes(self.account_statement_file)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            account_statement_id = self.env['account.statement'].browse(self._context.get('active_id')).id
            check_account = []
            check_pos_chop = []
            check_amount = []
            for i in range(1, sheet.nrows):
                pos_shop_code = sheet.cell_value(i, 3).split('/')[0]
                pos_shop_id = self.env['pos.shop'].search([('code', '=', pos_shop_code)]).id
                account_code = sheet.cell_value(i, 5)
                if type(account_code) == type(0.01):
                    account_code = int(account_code)
                account_id = self.env['account.account'].search([('code', '=', account_code)]).id
                if not pos_shop_id:
                    check_pos_chop.append(i + 1)
                if not account_id:
                    check_account.append(i + 1)
                if type(sheet.cell_value(i, 4)) != type(0.01) or sheet.cell_value(i, 4) <= 0:
                    check_amount.append(i + 1)

            list_check_pos_chop = ' , '.join([str(ps) for ps in check_pos_chop])
            list_check_account = ' , '.join([str(acc) for acc in check_account])
            list_check_amount = ' , '.join([str(amount) for amount in check_amount])
            mess_error = ''
            if list_check_pos_chop:
                mess_error += _('\nPos shop code does not exist in the system, line (%s)') % str(list_check_pos_chop)
            if list_check_account:
                mess_error += _('\nAccount accounting was not found in the system, line (%s)') % str(list_check_account)
            if list_check_amount:
                mess_error += _('\nAmount must be numeric and greater 0 , line (%s)') % str(list_check_amount)
            if mess_error:
                raise UserError(mess_error)
            else:
                for i in range(1, sheet.nrows):
                    pos_shop_code = sheet.cell_value(i, 3).split('/')[0]
                    date = sheet.cell_value(i, 1)
                    check_date = self.check_date(date)
                    if check_date == True:
                        date_time = datetime.fromordinal(
                            datetime(1900, 1, 1).toordinal() + int(sheet.cell_value(i, 1)) - 2)
                        date = datetime.strftime(date_time, '%Y-%m-%d')
                    else:
                        date = date.strip()
                        date = date.split('/')[2] + '-' + date.split('/')[1] + '-' + date.split('/')[0]
                    pos_shop = self.env['pos.shop'].search([('code', '=', pos_shop_code)])
                    account_analytic_id = pos_shop.analytic_account_id.id
                    account_code = sheet.cell_value(i, 5)
                    if type(account_code) == type(0.01):
                        account_code = int(account_code)
                    account_id = self.env['account.account'].search([('code', '=', account_code)]).id
                    self.env['account.statement.line'].create({
                        'account_statement_id': account_statement_id,
                        'code': sheet.cell_value(i, 0),
                        'date': date,
                        'name': sheet.cell_value(i, 2),
                        'description': sheet.cell_value(i, 3),
                        'amount': sheet.cell_value(i, 4),
                        'account_analytic_id': account_analytic_id,
                        'account_id': account_id,
                    })
                    self.env.cr.commit()
        except Exception as e:
            raise ValidationError(e)

    def check_date(self, date):
        try:
            date = int(date)
            return True
        except:
            return False

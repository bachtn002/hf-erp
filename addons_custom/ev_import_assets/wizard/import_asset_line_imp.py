import base64
import xlrd3
import pytz

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv
from datetime import datetime


class ImportAssetLineIMP(models.TransientModel):
    _name = 'import.asset.line.import'

    upload_file = fields.Binary(string="Upload File")
    template_file_url_default = fields.Char(default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
        'web.base.url') + '/ev_import_assets/static/imp_tsccdc.xlsx',
                                            string='Template File URL')

    def import_asset_line_imp(self):
        try:
            data = base64.decodebytes(self.upload_file)
            wb = xlrd3.open_workbook(file_contents=data)
        except:
            raise ValidationError(
                _("File not found or in incorrect format. Please check the .xls or .xlsx file format")
            )
        try:
            data = base64.decodebytes(self.upload_file)
            excel = xlrd3.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)

            check_asset_product = []
            check_quantity = []
            check_price_unit = []
            check_money_depreciation = []
            check_value = []
            check_method = []
            check_method_number = []
            check_asset_model = []
            check_account_id = []
            check_account_expense_id = []
            check_journal_id = []
            check_account_analytic_id = []
            check_account_expense_item_id = []
            check_account_asset_id = []
            check_date_buy = []
            check_date_depreciation_old = []
            check_date_depreciation_new = []
            import_asset = self.env['import.asset'].browse(self._context.get('active_id'))
            line_ids = []
            mess_error = ''
            for i in range(4, sheet.nrows):
                asset_product = self.env['product.product'].search(
                    [('default_code', '=', sheet.cell_value(i, 3))], limit = 1)
                asset_model = sheet.cell_value(i, 4)
                quantity = sheet.cell_value(i, 5)
                price_unit = sheet.cell_value(i, 6)
                money_depreciation = sheet.cell_value(i, 9)
                value = sheet.cell_value(i, 10)
                method = sheet.cell_value(i, 11)
                method_number = sheet.cell_value(i, 12)
                depreciation_number_import = sheet.cell_value(i, 13)
                account_id = sheet.cell_value(i, 15)
                account_expense_id = sheet.cell_value(i, 16)
                journal_id = sheet.cell_value(i, 17)
                account_analytic_id = sheet.cell_value(i, 18)
                account_expense_item_id = sheet.cell_value(i, 19)
                account_asset_id = sheet.cell_value(i, 20)
                # if not asset_product or not asset_product.active:
                #     check_asset_product.append(i + 1)

                if not self._is_number(quantity):
                    check_quantity.append(i + 1)
                if not self._is_number(price_unit):
                    check_price_unit.append(i + 1)
                if not self._is_number(money_depreciation):
                    check_money_depreciation.append(i + 1)
                if not self._is_number(value):
                    check_value.append(i + 1)

                if method != 'linear' and method != 'degressive' and method != 'degressive_then_linear':
                    check_method.append(i + 1)
                if not self._is_number(method_number):
                    check_method_number.append(i + 1)

                asset_model_id = self.env['account.asset'].search([('x_code','=',asset_model)], limit=1)
                # if not asset_model_id:
                #     check_asset_model.append(i + 1)

                account_id = self.env['account.account'].search(
                    [('code', '=', str(int(sheet.cell_value(i, 15))))], limit = 1)
                if not account_id:
                    check_account_id.append(i + 1)
                account_expense_id = self.env['account.account'].search(
                    [('code', '=', str(int(sheet.cell_value(i, 16))))], limit = 1)
                if not account_expense_id:
                    check_account_expense_id.append(i + 1)

                journal_id = self.env['account.journal'].search(
                    [('code', '=', sheet.cell_value(i, 17))], limit = 1)
                if not journal_id:
                    check_journal_id.append(i + 1)

                account_analytic_id = self.env['account.analytic.account'].search(
                    [('code', '=', sheet.cell_value(i, 18))], limit = 1)
                if not account_analytic_id:
                    check_account_analytic_id.append(i + 1)

                account_expense_item_id = self.env['account.expense.item'].search(
                    [('code', '=', sheet.cell_value(i, 19))], limit = 1)
                if not account_expense_item_id:
                    check_account_expense_item_id.append(i + 1)

                account_asset_id = self.env['account.account'].search(
                    [('code', '=', sheet.cell_value(i, 20))], limit = 1)
                if not account_asset_id:
                    check_account_asset_id.append(i + 1)

                inventory_loss_account_id = self.env['account.account'].search(
                    [('code', '=', sheet.cell_value(i, 21))], limit = 1)

                date_buy = sheet.cell_value(i, 7)
                if not self._is_date(date_buy):
                    check_date_buy.append(i + 1)
                else:
                    date_buy = datetime.fromordinal(
                        datetime(1900, 1, 1).toordinal() + int(date_buy) - 2)
                    date_buy = datetime.strftime(date_buy, '%Y-%m-%d')

                date_depreciation_old = sheet.cell_value(i, 8)
                if not self._is_date(date_depreciation_old):
                    check_date_depreciation_old.append(i + 1)
                else:
                    date_depreciation_old = datetime.fromordinal(
                        datetime(1900, 1, 1).toordinal() + int(date_depreciation_old) - 2)
                    date_depreciation_old = datetime.strftime(date_depreciation_old, '%Y-%m-%d')

                date_depreciation_new = sheet.cell_value(i, 14)
                if not self._is_date(date_depreciation_new):
                    check_date_depreciation_new.append(i + 1)
                else:
                    date_depreciation_new = datetime.fromordinal(
                        datetime(1900, 1, 1).toordinal() + int(date_depreciation_new) - 2)
                    date_depreciation_new = datetime.strftime(date_depreciation_new, '%Y-%m-%d')

                #list_check_asset_product = ' , '.join([str(id) for id in check_asset_product])
                list_check_quantity = ' , '.join([str(id) for id in check_quantity])
                list_check_price_unit = ' , '.join([str(id) for id in check_price_unit])
                list_check_money_depreciation = ' , '.join([str(id) for id in check_money_depreciation])
                list_check_value = ' , '.join([str(id) for id in check_value])
                list_check_method = ' , '.join([str(id) for id in check_method])
                list_check_method_number = ' , '.join([str(id) for id in check_method_number])
                #list_check_asset_model = ' , '.join([str(id) for id in check_asset_model])
                list_check_account_id = ' , '.join([str(id) for id in check_account_id])
                list_check_account_expense_id = ' , '.join([str(id) for id in check_account_expense_id])
                list_check_journal_id = ' , '.join([str(id) for id in check_journal_id])
                list_check_account_analytic_id = ' , '.join([str(id) for id in check_account_analytic_id])
                list_check_account_expense_item_id = ' , '.join([str(id) for id in check_account_expense_item_id])
                list_check_account_asset_id = ' , '.join([str(id) for id in check_account_asset_id])
                list_check_date_buy = ' , '.join([str(id) for id in check_date_buy])
                list_check_date_depreciation_old = ' , '.join([str(id) for id in check_date_depreciation_old])
                list_check_date_depreciation_new = ' , '.join([str(id) for id in check_date_depreciation_new])

                # if list_check_asset_product:
                #     mess_error += _('\nAsset product not exist in the system or not active, line (%s)') % str(
                #         list_check_asset_product)
                if list_check_quantity:
                    mess_error += _('\nQuantity not is number, line (%s)') % str(
                        list_check_quantity)
                if list_check_price_unit:
                    mess_error += _('\nPrice unit not is number, line (%s)') % str(
                        list_check_price_unit)
                if list_check_money_depreciation:
                    mess_error += _('\nMoney depreciation not is number, line (%s)') % str(
                        list_check_money_depreciation)
                if list_check_value:
                    mess_error += _('\nValue not is number, line (%s)') % str(
                        list_check_value)
                if list_check_method:
                    mess_error += _('\nMethod not exist in asset, line (%s)') % str(
                        list_check_method)
                if list_check_method_number:
                    mess_error += _('\nMethod number not is number, line (%s)') % str(
                        list_check_method_number)
                # if list_check_asset_model:
                #     mess_error += _('\nAsset Model not exist in the system, line (%s)') % str(
                #         list_check_asset_model)
                if list_check_account_id:
                    mess_error += _('\nAccount not exist in the system, line (%s)') % str(
                        list_check_account_id)
                if list_check_account_expense_id:
                    mess_error += _('\nAccount expense not exist in the system, line (%s)') % str(
                        list_check_account_expense_id)
                if list_check_journal_id:
                    mess_error += _('\nJournal not exist in the system, line (%s)') % str(
                        list_check_journal_id)
                if list_check_account_analytic_id:
                    mess_error += _('\nAccount analytic not exist in the system, line (%s)') % str(
                        list_check_account_analytic_id)
                if list_check_account_expense_item_id:
                    mess_error += _('\nAccount expense item not exist in the system, line (%s)') % str(
                        list_check_account_expense_item_id)
                if list_check_account_asset_id:
                    mess_error += _('\nAccount asset not exist in the system, line (%s)') % str(
                        list_check_account_asset_id)
                if list_check_date_buy:
                    mess_error += _('\nDate buy not is date, line (%s)') % str(
                        list_check_date_buy)
                if list_check_date_depreciation_old:
                    mess_error += _('\nDatereciation old not is date, line (%s)') % str(
                        list_check_date_depreciation_old)
                if list_check_date_depreciation_new:
                    mess_error += _('\nDate depreciton new not is date, line (%s)') % str(
                        list_check_date_depreciation_new)

                line = {
                    'name': sheet.cell_value(i, 1),
                    'code': sheet.cell_value(i, 2),
                    'asset_product_id': asset_product.id if asset_product else None,
                    'asset_model_id': sheet.cell_value(i, 5),
                    'quantity': quantity,
                    'price_unit': price_unit,
                    'date_buy': date_buy,
                    'date_depreciation_old': date_depreciation_old,
                    'money_depreciation': money_depreciation,
                    'value': value,
                    'method_depreciation': method,
                    'method_number': method_number,
                    'date_depreciation_new': date_depreciation_new,
                    'asset_model_id': asset_model_id.id if asset_model else None,
                    'account_id': account_id.id,
                    'account_expense_id': account_expense_id.id,
                    'journal_id': journal_id.id,
                    'account_analytic_id': account_analytic_id.id,
                    'account_expense_item_id': account_expense_item_id.id,
                    'account_asset_id': account_asset_id.id,
                    'import_asset_id': import_asset.id,
                    'inventory_loss_account_id': inventory_loss_account_id.id,
                    'depreciation_number_import': depreciation_number_import,
                    'asset_type': sheet.cell_value(i, 22)
                }
                line_ids.append((0, 0, line))
            if mess_error:
                raise UserError(mess_error)
            else:
                import_asset.line_ids = line_ids

        except Exception as e:
            raise ValidationError(e)

    def _is_number(self, name):
        try:
            float(name)
            return True
        except ValueError:
            return False

    def _is_date(self, date):
        try:
            int(date)
            return True
        except ValueError:
            return False

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import osv
import base64
import xlrd


class ImportPhonePromotionRelease(models.TransientModel):
    _name = "import.phone.promotion.release"
    _description = "Import phone promotion release"

    file_import = fields.Binary('File import', help="File to check and/or import, raw binary (not base64)",
                                attachment=False)
    file_name = fields.Char('File Name')

    file_import_type = fields.Selection(string="File import type",
                                        selection=[('phone', 'Phone'), ('phone_code', 'Phone code')], default='phone',
                                        required=1)

    promotion_voucher_id = fields.Many2one('promotion.voucher', "Promotion voucher")

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def _get_data_phone(self):
        try:
            if not self._check_format_excel(self.file_name):
                raise ValidationError(_("File not found or extension invalid (only accept .xls or .xlsx"))
            data_base64 = base64.decodestring(self.file_import)
            book = xlrd.open_workbook(file_contents=data_base64)
            sheet = book.sheet_by_index(0)
            # Check tổng số mã * số lần sử dụng >= Tổng số điện thoại (-1 dòng label)
            if sheet.nrows - 1 > self.promotion_voucher_id.quantity * self.promotion_voucher_id.promotion_use_code:
                raise ValidationError(_("There is not enough promotion code for list phone number!"))
            data = []
            phone_list = []
            messages = ''
            row = 1
            while row < sheet.nrows:
                phone_number = sheet.cell(row, 0).value.replace(' ', '')

                if not phone_number:
                    messages += '\n '
                    messages += _("Missing required phone number in row %s") % (row + 1)
                else:
                    if type(phone_number).__name__ in ['int', 'float']:
                        phone_number = str(int(phone_number))
                    else:
                        phone_number = str(phone_number)
                    if not phone_number.isnumeric():
                        messages += '\n '
                        messages += _("Phone number is not valid in row %s") % (row + 1)
                    if len(phone_number) < 6 or len(phone_number) > 15:
                        messages += '\n '
                        messages += _("Phone number length must be between [6,15] in %s") % (row + 1)
                    # Check duplicate phone number
                    if phone_number in phone_list:
                        messages += '\n '
                        messages += _("Duplicate phone number %s") % (phone_number)
                    else:
                        phone_list.append(phone_number)

                vals = {
                    'phone': phone_number,
                    'promotion_voucher_id': self.promotion_voucher_id.id,
                    'state': 'new'
                }
                data.append(vals)
                row += 1
            return data, messages
        except Exception as e:
            raise UserError(_("Warning: %s") %e)

    def _get_data_phone_code(self):
        try:
            if not self._check_format_excel(self.file_name):
                raise ValidationError(_("File not found or extension invalid (only accept .xls or .xlsx"))
            data_base64 = base64.decodestring(self.file_import)
            book = xlrd.open_workbook(file_contents=data_base64)
            sheet = book.sheet_by_index(0)
            # Check tổng số mã * số lần sử dụng >= Tổng số điện thoại
            if sheet.nrows -1 > self.promotion_voucher_id.quantity * self.promotion_voucher_id.promotion_use_code:
                raise ValidationError(_("There is not enough promotion code for list phone number!"))
            promotion_code_list = self.promotion_voucher_id.promotion_voucher_line.mapped('name')
            data = []
            # phone_list = []
            messages = ''
            row = 1
            while row < sheet.nrows:
                promotion_code = sheet.cell(row, 0).value.replace(' ', '')
                phone_number = sheet.cell(row, 1).value.replace(' ', '')

                if not promotion_code:
                    messages += '\n '
                    messages += _('Missing code in row %s') % (row + 1)
                # Check code import phải nằm trong danh sách code đã được gen
                elif promotion_code not in promotion_code_list:
                    messages += '\n '
                    messages += _("Promotion code is not exist in those codes generated in row %s") % (row + 1)

                if not phone_number:
                    messages += '\n '
                    messages += _("Missing required phone number in row %s") % (row + 1)
                else:
                    if type(phone_number).__name__ in ['int', 'float']:
                        phone_number = str(int(phone_number))
                    else:
                        phone_number = str(phone_number)
                    if not phone_number.isnumeric():
                        messages += '\n '
                        messages += _("Phone number must be number type in row %s")% (row + 1)
                    if len(phone_number) < 6 or len(phone_number) > 15:
                        messages += '\n '
                        messages += _("Phone number length must be between [6,15] in %s") % (row + 1)
                    # Check duplicate phone number
                    # if phone_number in phone_list:
                    #     messages += '\n '
                    #     messages += _("Duplicate phone number %s") % (phone_number)
                    # else:
                    # phone_list.append(phone_number)

                vals = {
                    'promotion_code': promotion_code,
                    'phone': phone_number,
                    'promotion_voucher_id': self.promotion_voucher_id.id,
                    'state': 'available'
                }
                data.append(vals)
                row += 1
            return data, messages
        except Exception as e:
            raise UserError(_("Warning: %s") %e)

    def action_import(self):
        if self.file_import_type == 'phone':
            datas, messages = self._get_data_phone()
        else:
            datas, messages = self._get_data_phone_code()
        if messages or messages != '':
            raise ValidationError(messages)
        else:
            self.promotion_voucher_id.x_phone_promotion_list_ids = False
            if self.file_import_type != 'phone':
                self.promotion_voucher_id.x_is_phone_release = True
            self.env['phone.promotion.list'].create(datas)

    def download_template_phone(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_promotion_phone_release/static/template/template_phone.xlsx',
            "target": "_parent",
        }

    def download_template_phone_code(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_promotion_phone_release/static/template/template_phone_code.xlsx',
            "target": "_parent",
        }

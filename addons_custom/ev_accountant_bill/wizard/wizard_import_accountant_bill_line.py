# -*- coding: utf-8 -*-

from datetime import datetime, date
from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import xlrd


class WizardImportAccountantBillLine(models.TransientModel):
    _name = 'wizard.import.accountant.bill.line'

    _inherits = {'ir.attachment': 'attachment_id'}

    import_date = fields.Date(required=False, default=date.today(), string='Import Date')
    template_file_url_default = fields.Char(default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
        'web.base.url') + '/ev_accountant_bill/static/Template_import_phieu_ke_toan.xls',
                                            string='Template File URL')
    order_id = fields.Many2one('accountant.bill')

    def action_import_ab_line(self):
        self.ensure_one()
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/wizard_import_accountant_bill_line_template_' + user.login + '_' + str(self[0].id) + '_' + str(
            datetime.now()).replace(":", '_') + '.xls'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)
        if len(excel_data) < 2:
            raise ValidationError(_('File excel phải có ít nhất 1 dòng sau tiêu đề!'))
        excel_data = excel_data[1:]
        row_number = 2
        for row in excel_data:
            value = {'accountant_bill_id': self.order_id.id, 'company_id': self.order_id.company_id.id,
                     'currency_id': self.order_id.currency_id.id}
            space = len('Row{}: '.format(row_number)) + 8

            if not row[0]:
                raise ValidationError(
                    "Dòng %s: Bạn cần nhập diễn giải" % (row_number))
            else:
                name = str(row[0])
                value.update({'name': name})

            if row[1]:
                purchase_order = self.env['purchase.order'].search([('origin', '=', str(row[1]))])
                if purchase_order:
                    value.update({'purchase_order_id': purchase_order.id, '': row[1]})
                else:
                    raise ValidationError(
                        "Dòng %s: Không có mã hợp đồng %s trong hệ thống" % (row_number, str(row[1])))

            if row[2]:
                res_partner = self.env['res.partner'].search([('ref', '=', str(row[2]))])
                if res_partner:
                    value.update({'debit_partner_id': res_partner.id})
                else:
                    raise ValidationError(
                        "Dòng %s: Không tìm thấy đối tác bên nợ với mã %s trong hệ thống" % (row_number, str(row[2])))

            if row[3]:
                res_partner = self.env['res.partner'].search([('ref', '=', str(row[3]))])
                if res_partner:
                    value.update({'credit_partner_id': res_partner.id})
                else:
                    raise ValidationError(
                        "Dòng %s: Không tìm thấy đối tác bên có với mã %s trong hệ thống" % (row_number, str(row[3])))

            if row[4]:
                account_id = self.env['account.account'].search([('code', '=', int(row[4]))])
                if account_id:
                    value.update({'debit_acc_id': account_id.id})
                else:
                    raise ValidationError(
                        "Dòng %s: Không tìm thấy tài khoản nợ với mã %s trong hệ thống" % (row_number, str(row[4])))
            else:
                raise ValidationError("Dòng %s: Bạn cần phải nhập tài khoản bên nợ" % row_number)

            if row[5]:
                account_id = self.env['account.account'].search([('code', '=', int(row[5]))])
                if account_id:
                    value.update({'credit_acc_id': account_id.id})
                else:
                    raise ValidationError(
                        "Dòng %s: Không tìm thấy tài khoản có với mã %s trong hệ thống" % (row_number, str(row[5])))
            else:
                raise ValidationError("Dòng %s:Bạn cần phải nhập tài khoản bên có" % row_number)

            if row[6]:
                x = row[6]
                if isinstance(x, float):
                    value.update({'value': x})
                    if self.order_id.company_id.currency_id == self.order_id.currency_id:
                        value.update({'value_natural_currency': x})
                    else:
                        value.update({'value_natural_currency': (x * self.order_id.rate)})
                else:
                    raise ValidationError("Dòng %s:Sai định dạng cột giá trị" % row_number)

            if row[7]:
                res_partner = self.env['res.partner'].search([('ref', '=', str(row[7]))])
                if res_partner:
                    value.update({'part_id': res_partner.id})
                else:
                    raise ValidationError(
                        "Dòng %s:Không tìm thấy bộ phận với mã %s trong hệ thống" % (row_number, str(row[7])))

            if row[8]:
                analytic_account_id = self.env['account.analytic.account'].search([('code', '=', str(row[8]))])
                if analytic_account_id:
                    value.update({'analytic_account_id': analytic_account_id.id})
                else:
                    raise ValidationError(
                        "Dòng %s:Không tìm thấy Khoản mục phí với mã %s trong hệ thống" % (row_number, str(row[8])))

            if row[9]:
                object_cost_id = self.env['object.cost'].search([('name', '=', str(row[9]))])
                if object_cost_id:
                    value.update({'object_cost_id': object_cost_id.id})
                else:
                    raise ValidationError(
                        "Dòng %s:Không tìm thấy Đối tượng THCP với mã %s trong hệ thống" % (row_number, str(row[9])))

            line = self.env['accountant.bill.line'].create(value)
            row_number += 1

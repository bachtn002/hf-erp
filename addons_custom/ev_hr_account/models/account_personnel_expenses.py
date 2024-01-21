# -*- coding: utf-8 -*-

import base64

import xlrd

from odoo import models, fields, api, _
from odoo.osv import osv
from odoo.exceptions import UserError


class AccountPersonnelExpenses(models.Model):
    _name = 'account.personnel.expenses'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Personnel Expenses'

    def _compute_amount_total(self):
        for order in self:
            amount = 0.0
            for line in order.lines:
                amount += line.amount
            order.update({
                'amount_total': amount,
            })

    name = fields.Char(string="Name", track_visibility='always')
    expenses_number = fields.Char(string="Expenses Number", track_visibility='always')
    date_from = fields.Date(string="Date From", track_visibility='always')
    date_to = fields.Date(string="Date To", track_visibility='always')
    account_fiscal_month_id = fields.Many2one('account.fiscal.month', 'Accounting Period')
    date_document = fields.Date(string="Date Document", track_visibility='always')
    date_accounting = fields.Date(string="Date Accounting", track_visibility='always')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string="State", default='draft',
                             track_visibility='always')
    lines = fields.One2many('account.personnel.expenses.line', 'expenses_id', string="Expenses Lines",
                            track_visibility='always', copy=True)
    field_binary = fields.Binary(string="Field Binary")
    field_binary_name = fields.Char(string="Field Binary Name")
    journal_id = fields.Many2one('account.journal', string="Journal", track_visibility='always')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id.id)
    move_ids = fields.One2many('account.move', 'x_personnel_expenses_id', string="Account Moves")
    total_entries = fields.Integer(string="Total Entries", compute="_compute_total_entry", track_visibility='always')
    description = fields.Text('Description')
    amount_total = fields.Float('Amount Total', compute='_compute_amount_total')

    _sql_constraints = [
        ('expenses_number_uniq', 'unique (expenses_number)', 'The expenses number of the account personnel expenses must be unique!')
    ]

    def _compute_amount_total(self):
        for order in self:
            amount = 0.0
            for line in order.lines:
                amount += line.amount
            order.amount_total= amount

    def _compute_total_entry(self):
        for record in self:
            move_ids = self.env['account.move'].search([('x_personnel_expenses_id', '=', record.id)])
            record.total_entries = len(move_ids)

    def action_view_move(self):
        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        result['domain'] = "[('id', 'in', " + str(self.move_ids.ids) + ")]"
        return result

    def unlink(self):
        if self.state == 'draft':
            return super(AccountPersonnelExpenses, self).unlink()
        raise UserError(_('Thông báo'), ('Bạn chỉ có thể xóa khi ở trạng thái Nháp'))

    def action_download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_hr_account/static/template/personnel_expenses_template.xlsx',
            "target": "_parent",
        }

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def action_import(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodebytes(self.field_binary)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            PartnerObj = self.env['res.partner']
            AnalyticObj = self.env['account.analytic.account']
            FeeItemObj = self.env['account.expense.item']
            AccountObj = self.env['account.account']
            vals = []
            while index < sheet.nrows:
                # init object
                part_id = None
                partner_id = None
                analytic_id = None
                fee_item_id = None
                # read column from excel file
                part_code = sheet.cell(index, 0).value
                part_name = sheet.cell(index, 1).value
                if part_code and len(part_code) > 0:
                    part_code = str(part_code).strip()

                    part_id = PartnerObj.search(['|', '|', '|', ('ref', '=', part_code), ('email', '=', part_code),
                         ('phone', '=', part_code), ('mobile', '=', part_code)], limit=1)
                    if len(part_id) == 0:
                        raise osv.except_osv("Cảnh báo!",
                                             ("Mã bộ phận " + str(part_code) + " không tồn tại, tại dòng thứ " + str(
                                                 index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))
                elif part_name and len(part_name) > 0:
                    part_name = str(part_name).strip()

                    part_id = PartnerObj.search([('name', '=', part_name)], limit=1)
                    if len(part_id) == 0:
                        raise osv.except_osv("Cảnh báo!",
                                             ("Tên bộ phận " + str(part_name) + " không tồn tại, tại dòng thứ " + str(
                                                 index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))

                partner_code = sheet.cell(index, 2).value
                partner_name = sheet.cell(index, 3).value
                if partner_code and len(str(partner_code)) > 0:
                    partner_code = str(partner_code).strip()
                    partner_id = PartnerObj.search(
                        ['|', '|', '|', ('ref', '=', partner_code), ('email', '=', partner_code),
                         ('phone', '=', partner_code), ('mobile', '=', partner_code)], limit=1)
                    if len(partner_id) == 0:
                        raise osv.except_osv("Cảnh báo!",
                                             ("Mã đối tác " + str(partner_code) + " không tồn tại, tại dòng thứ " + str(
                                                 index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))
                elif partner_name and len(str(partner_name)) > 0:
                    partner_name = str(partner_name).strip()
                    partner_id = PartnerObj.search([('name', '=', partner_name)], limit=1)
                    if len(partner_id) == 0:
                        raise osv.except_osv("Cảnh báo!",
                                             ("Tên đối tác " + str(partner_name) + " không tồn tại, tại dòng thứ " + str(
                                                 index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))

                analytic_name = sheet.cell(index, 4).value
                if analytic_name and len(str(analytic_name)) > 0:
                    analytic_name = str(analytic_name).strip()
                    analytic_id = AnalyticObj.search([('name', '=', analytic_name)], limit=1)
                    if len(analytic_id) == 0:
                        raise osv.except_osv("Cảnh báo!",
                                             ("Khoản mục phí " + str(analytic_name) + " không tồn tại, tại dòng thứ " + str(
                                                 index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))

                item_name = sheet.cell(index, 5).value
                if item_name and len(str(item_name)) > 0:
                    item_name = str(item_name).strip()
                    fee_item_id = FeeItemObj.search([('name', '=', item_name)], limit=1)
                    if len(fee_item_id) == 0:
                        raise osv.except_osv("Cảnh báo!",
                                             ("Mã đối tượng tập hợp chi phí " + str(
                                                 item_name) + " không tồn tại, tại dòng thứ " + str(
                                                 index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))

                debit_code = sheet.cell(index, 6).value
                if debit_code == "":
                    raise osv.except_osv("Cảnh báo!",
                                         ("Mã tài khoản nợ không được để trống, tại dòng thứ " + str(
                                             index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))
                debit_code = str(int(debit_code)).strip()
                debit_acc_id = AccountObj.search([('code', '=', debit_code)], limit=1)
                if len(debit_acc_id) == 0:
                    raise osv.except_osv("Cảnh báo!",
                                         ("Mã tài khoản nợ " + str(
                                             debit_code) + " không tồn tại, tại dòng thứ " + str(
                                             index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))

                credit_code = sheet.cell(index, 7).value
                if credit_code == "":
                    raise osv.except_osv("Cảnh báo!",
                                         ("Mã tài khoản có không được để trống, tại dòng thứ " + str(
                                             index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))
                credit_code = str(int(credit_code)).strip()
                credit_acc_id = AccountObj.search([('code', '=', credit_code)], limit=1)
                if len(credit_acc_id) == 0:
                    raise osv.except_osv("Cảnh báo!",
                                         ("Mã tài khoản có " + str(
                                             credit_code) + " không tồn tại, tại dòng thứ " + str(
                                             index) + ". Vui lòng kiểm tra lại. Xin cảm ơn."))
                value = sheet.cell(index, 8).value
                if not self.is_number(value):
                    raise osv.except_orm('Cảnh báo', 'Số tiền không đúng định dạng số tại dòng thứ ' + str(
                        index) + ' không tồn tại. Vui lòng kiểm tra lại. Xin cảm ơn')
                # verify data excel
                vals.append((0,0,{
                    'part_id': part_id.id if part_id else None,
                    'debit_acc_id': debit_acc_id.id,
                    'credit_acc_id': credit_acc_id.id,
                    'partner_id': partner_id.id if partner_id else None,
                    'analytic_id': analytic_id.id if analytic_id else None,
                    'fee_item': fee_item_id.id if fee_item_id else None,
                    'amount': value
                }))
                index = index + 1
            self.lines = vals
            self.field_binary = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def action_done(self):
        if self.state == 'done':
            return
        AccountMoveObj = self.env['account.move']
        company_id = self.company_id.id or self.env.user.company_id.id
        for expense_line in self.lines:
            move_lines = []
            debit_line_vals = {
                'name': self.name,
                'ref': self.name,
                'partner_id': expense_line.partner_id.id if expense_line.partner_id.id else None,
                'analytic_account_id': expense_line.analytic_id.id if expense_line.analytic_id.id else None,
                'x_fee_item_id': expense_line.fee_item.id if expense_line.fee_item.id else None,
                'debit': expense_line.amount if expense_line.amount > 0 else abs(expense_line.amount),
                'credit': 0,
                'account_id': expense_line.debit_acc_id.id,
                'company_id': company_id,
            }
            credit_line_vals = {
                'name': self.name,
                'ref': self.name,
                'credit': expense_line.amount if expense_line.amount > 0 else abs(expense_line.amount),
                'partner_id': expense_line.partner_id.id if expense_line.partner_id.id else None,
                'analytic_account_id': expense_line.analytic_id.id if expense_line.analytic_id.id else None,
                'x_fee_item_id': expense_line.fee_item.id if expense_line.fee_item.id else None,
                'debit': 0,
                'account_id': expense_line.credit_acc_id.id,
                'company_id': company_id,
            }
            if expense_line.part_id:
                debit_line_vals['x_part_id'] = expense_line.part_id.id
                credit_line_vals['x_part_id'] = expense_line.part_id.id
            move_lines.append((0, 0, debit_line_vals))
            move_lines.append((0, 0, credit_line_vals))
            move_vals = {
                'ref': self.name,
                'date': self.date_accounting,
                'journal_id': self.journal_id.id,
                'line_ids': move_lines,
                'company_id': company_id,
                'x_personnel_expenses_id': self.id
            }
            move_id = AccountMoveObj.create(move_vals)
            move_id.post()
            expense_line.move_id = move_id.id
        self.state = 'done'

    def action_cancel(self):
        if len(self.move_ids) > 0:
            move_ids = self.move_ids.with_context(force_delete=True)
            move_ids.button_cancel()
            move_ids.unlink()
        self.state = 'draft'


class AccountPersonnelExpensesLine(models.Model):
    _name = 'account.personnel.expenses.line'
    _description = 'Expenses Lines'

    expenses_id = fields.Many2one('account.personnel.expenses', string="Personnel Expenses")
    debit_acc_id = fields.Many2one('account.account', string="Debit Account")
    credit_acc_id = fields.Many2one('account.account', string="Credit Account")
    partner_id = fields.Many2one('res.partner', string="Partner")
    part_id = fields.Many2one('res.partner', 'Part')
    analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    fee_item = fields.Many2one('account.expense.item', string='Fee Item')
    object_id = fields.Many2one('object.cost', string="Object Cost")
    amount = fields.Float(string="Amount")
    move_id = fields.Many2one('account.move', string="Account Move Ref")

    def action_show_details(self):
        view = self.env.ref('account.view_move_form')
        if self.move_id.id:
            return {
                'name': _('Journal Entry'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.move_id.id,
            }
        else:
            raise osv.except_osv("Cảnh báo!",
                                 ("Không tìm thấy bút toán cho hạch toán chi phí này"))

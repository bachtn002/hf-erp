# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, except_orm
from odoo.osv import osv
import xlrd
import base64

ones = ["", "một ", "hai ", "ba ", "bốn ", "năm ", "sáu ", "bảy ", "tám ", "chín ", "mười ", "mười một ", "mười hai ",
        "mười ba ", "mười bốn ", "mười lăm ", "mười sáu ", "mười bảy ", "mười tám ", "mười chín "]
twenties = ["", "", "hai mươi ", "ba mươi ", "bốn mươi ", "năm mươi ", "sáu mươi ", "bảy mươi ", "tám mươi ",
            "chín mươi "]
thousands = ["", "nghìn ", "triệu ", "tỉ ", "nghìn ", "triệu ", "tỉ "]


def _is_number(name):
    try:
        float(name)
        return True
    except ValueError:
        return False


def _check_format_excel(file_name):
    if not file_name:
        return False
    if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
        return False
    return True


def num999(n, next):
    c = n % 10  # singles digit
    b = int(((n % 100) - c) / 10)  # tens digit
    a = int(((n % 1000) - (b * 10) - c) / 100)  # hundreds digit
    t = ""
    h = ""
    if a != 0 and b == 0 and c == 0:
        t = ones[a] + "trăm "
    elif a != 0:
        t = ones[a] + "trăm "
    elif a == 0 and b == 0 and c == 0:
        t = ""
    elif a == 0 and next != '':
        t = "không trăm "
    if b == 1:
        h = ones[n % 100]
    if b == 0:
        if a > 0 and c > 0:
            h = "linh " + ones[n % 100]
        else:
            h = ones[n % 100]
    elif b > 1:
        if c == 4:
            tmp = "tư "
        elif c == 1:
            tmp = "mốt "
        else:
            tmp = ones[c]
        h = twenties[b] + tmp
    st = t + h
    return st


def num2word(num):
    if not isinstance(num, int):
        raise ValidationError("Number to convert to words must be integer")
    if num == 0: return 'không'
    i = 3
    n = str(num)
    word = ""
    k = 0
    while (i == 3):
        nw = n[-i:]
        n = n[:-i]
        int_nw = int(float(nw))
        if int_nw == 0:
            word = num999(int_nw, n) + thousands[int_nw] + word
        else:
            word = num999(int_nw, n) + thousands[k] + word
        if n == '':
            i += 1
        k += 1
    return word[:-1].capitalize()


class AccountantBill(models.Model):
    _name = 'accountant.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        return self.env.company.id

    @api.depends('lines.value')
    def _amount_all(self):
        for order in self:
            amount = 0.0
            amount_natural_currency = 0.0
            for line in order.lines:
                amount += line.value
                amount_natural_currency += line.value_natural_currency
            order.update({
                'amount': order.currency_id.round(amount),
                'amount_natural_currency': order.company_id.currency_id.round(amount_natural_currency)
            })

    name = fields.Char('Name', track_visibility='onchange', default=lambda self: _('New'), copy=False)
    date = fields.Date('Date', track_visibility='always', default=fields.Date.today())
    date_accounting = fields.Date('Date Accounting', track_visibility='always', default=fields.Date.today())
    date_document = fields.Date('Date Document', track_visibility='always', default=fields.Date.today())
    journal_id = fields.Many2one('account.journal', 'Journal', copy=False)
    description = fields.Text('Description')
    lines = fields.One2many('accountant.bill.line', 'accountant_bill_id', 'Lines', copy=True)
    company_id = fields.Many2one('res.company', 'Company', default=_default_company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  help="The optional other currency if it is a multi-currency entry.")
    amount = fields.Monetary(string='Amount', store=True, compute='_amount_all')
    amount_natural_currency = fields.Float(string='Amount Natural Currency', store=True, compute='_amount_all')
    rate = fields.Float('Rate')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    move_ids = fields.One2many('account.move', 'x_accountant_bill_id', 'Account Move')
    total_entries = fields.Integer(string="Total Entries", compute="_compute_total_entry", track_visibility='always')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancel')
    ], default='draft', copy=False)
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    @api.onchange('currency_id')
    def onchange_currency(self):
        if self.currency_id:
            for line in self.lines:
                line.currency_id = self.currency_id

    @api.onchange('rate')
    def onchange_rate(self):
        if self.rate:
            for line in self.lines:
                line.rate = self.rate

    def _compute_total_entry(self):
        for record in self:
            move_ids = self.env['account.move'].search([('x_accountant_bill_id', '=', record.id)])
            record.total_entries = len(move_ids)

    def action_view_move(self):
        action = self.env.ref('account.action_move_line_form').sudo()
        result = action.read()[0]
        result['domain'] = "[('id', 'in', " + str(self.move_ids.ids) + ")]"
        return result

    def unlink(self):
        if self.state == 'draft':
            return super(AccountantBill, self).unlink()
        raise UserError('Bạn chỉ có thể xóa khi ở trạng thái Nháp')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('accountant.bill') or _('New')
        return super(AccountantBill, self).create(vals)

    def action_confirm(self):
        self.ensure_one()

        move_lines = []
        for line in self.lines:
            if line.value <= 0:
                raise UserError("Total amount must be greater than 0")
            line.currency_id = self.currency_id
            # Ghi sổ trả/nhận của các đối tác
            debit_move_vals = {
                'name': line.name,
                'ref': self.name,
                'date': self.date_accounting,
                'account_id': line.debit_acc_id.id,
                'contra_account_id': line.credit_acc_id.id,
                'debit': line.value_natural_currency if line.value_natural_currency != 0 else line.value,
                'credit': 0.0,
                'partner_id': line.debit_partner_id.id if line.debit_partner_id else None,
                'quantity': line.quantity
            }
            if line.currency_id.id != self.company_id.currency_id.id:
                debit_move_vals['currency_id'] = line.currency_id.id
                debit_move_vals['amount_currency'] = line.value
            if line.analytic_account_id.id:
                debit_move_vals['analytic_account_id'] = line.analytic_account_id.id
            if line.debit_acc_id.user_type_id.type in ('receivable', 'payable'):
                debit_move_vals['date_maturity'] = self.date_accounting
            if line.account_expense_item_id.id:
                debit_move_vals['x_account_expense_item_id'] = line.account_expense_item_id.id
            if line.product_id.id:
                debit_move_vals['product_id'] = line.product_id.id
                debit_move_vals['product_uom_id'] = line.product_id.product_tmpl_id.uom_id.id
            move_lines.append((0, 0, debit_move_vals))

            # Ghi sổ thu/chi của công ty
            credit_move_vals = {
                'ref': self.name,
                'name': line.name,
                'date': self.date_accounting,
                'account_id': line.credit_acc_id.id,
                'contra_account_id': line.debit_acc_id.id,
                'debit': 0.0,
                'credit': line.value_natural_currency if line.value_natural_currency != 0 else line.value,
                'partner_id': line.credit_partner_id.id if line.credit_partner_id else None,
                'quantity': -line.quantity
            }
            if line.currency_id.id != self.company_id.currency_id.id:
                credit_move_vals['currency_id'] = line.currency_id.x_base_currency_id.id
                credit_move_vals['amount_currency'] = -line.value
            if line.analytic_account_id.id:
                credit_move_vals['analytic_account_id'] = line.analytic_account_id.id
            if line.credit_acc_id.user_type_id.type in ('receivable', 'payable'):
                credit_move_vals['date_maturity'] = self.date_accounting
            if line.account_expense_item_id.id:
                credit_move_vals['x_account_expense_item_id'] = line.account_expense_item_id.id
            if line.product_id.id:
                credit_move_vals['product_id'] = line.product_id.id
                credit_move_vals['product_uom_id'] = line.product_id.product_tmpl_id.uom_id.id
            move_lines.append((0, 0, credit_move_vals))

        move_vals = {
            'ref': self.name,
            'date': self.date_accounting,
            'journal_id': self.journal_id.id,
            'line_ids': move_lines,
            'x_accountant_bill_id': self.id
        }
        move_id = self.env['account.move'].create(move_vals)
        move_id.post()
        self.write({'state': 'posted'})
        return True

    def action_back(self):
        self.ensure_one()
        if len(self.move_ids) > 0:
            move_ids = self.move_ids.with_context(force_delete=True)
            move_ids.button_cancel()
            move_ids.unlink()
        self.state = 'draft'

    def button_open_wizard_import_accountant_bill_line(self):
        self.ensure_one()
        return {
            'name': _(''),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.import.accountant.bill.line',
            'no_destroy': True,
            'target': 'new',
            'view_id': self.env.ref('ev_accountant_bill.wizard_import_accountant_bill_line_form') and self.env.ref(
                'ev_accountant_bill.wizard_import_accountant_bill_line_form').id or False,
            'context': {'default_order_id': self.id},
        }

    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            self.date_accounting = self.date_document = self.date

    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_accountant_bill.report_accountant_bill/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def get_rate(self):
        _rate = '{0:,.0f}'.format(self.rate)
        return _rate

    def get_amount(self):
        _amount = 0
        if self.currency_id.name == 'USD':
            _amount = '{0:,.2f}'.format(self.amount)
        elif self.currency_id.name == 'VND':
            _amount = '{0:,.0f}'.format(self.amount)
        else:
            _amount = '{0:,.0f}'.format(self.amount)
        return _amount

    def get_amount_natural_currency(self):
        _amount_natural_currency = '{0:,.0f}'.format(self.amount_natural_currency)
        return _amount_natural_currency

    def get_amount_tax(self):
        _amount_tax = 0
        if self.currency_id.name == 'USD':
            _amount_tax = '{0:,.2f}'.format(self.amount_tax)
        elif self.currency_id.name == 'VND':
            _amount_tax = '{0:,.0f}'.format(self.amount_tax)
        else:
            _amount_tax = '{0:,.0f}'.format(self.amount_tax)
        return _amount_tax

    def get_amount_total(self):
        _amount_total = '{0:,.0f}'.format(self.amount_natural_currency)
        return _amount_total

    def get_amount_word(self, amount):
        res = num2word(int(amount)) + " đồng chẵn."
        return res

    def get_data_report(self):
        if self.state == 'posted':
            if self.move_ids.filtered(lambda m: m.state == 'posted'):
                return self.move_ids.filtered(lambda m: m.state == 'posted').mapped('line_ids')
        else:
            raise UserError('Không thể in ở trạng thái dự thảo. Vui lòng xác nhận phiếu')

    def action_import_line(self):
        try:
            if not _check_format_excel(self.field_binary_name):
                raise UserError(_('File format must be .xls or .xlsx'))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            self.lines.unlink()
            error_name_empty = []
            error_debit_account_empty = []
            error_credit_account_empty = []
            error_debit_account_not_exists = []
            error_credit_account_not_exists = []
            error_product_not_exists = []
            error_account_expense_not_exists = []
            error_product_empty = []
            error_analytic_account_empty = []
            error_analytic_account_not_exists = []
            error_account_expense_empty = []
            error_invalid_value = []
            error_value_greater = []
            error_value_empty = []

            while index < sheet.nrows:
                name = sheet.cell(index, 0).value
                if not name:
                    error_name_empty.append(index + 1)
                debit_acc_code = sheet.cell(index, 5).value
                credit_acc_code = sheet.cell(index, 6).value
                if not debit_acc_code:
                    error_debit_account_empty.append(index + 1)
                if not credit_acc_code:
                    error_credit_account_empty.append(index + 1)
                debit_acc_id = self.env['account.account'].search(
                    [('code', '=', debit_acc_code)], limit=1)
                if not debit_acc_id:
                    error_debit_account_not_exists.append(index + 1)
                credit_acc_id = self.env['account.account'].search(
                    [('code', '=', credit_acc_code)], limit=1)
                if not credit_acc_id:
                    error_credit_account_not_exists.append(index + 1)
                product_code = str(sheet.cell_value(index, 1)).split('.')[0]
                product_id = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                if not product_id and product_code:
                    error_product_not_exists.append(index + 1)
                account_expense_item_code = sheet.cell(index, 2).value
                account_expense_item_id = self.env['account.expense.item'].search(
                    [('code', '=', str(account_expense_item_code))], limit=1)
                if not account_expense_item_id and account_expense_item_code:
                    error_account_expense_not_exists.append(index + 1)
                analytic_account_code = sheet.cell(index, 8).value
                analytic_account_id = self.env['account.analytic.account'].search(
                    [('code', '=', analytic_account_code)], limit=1)
                if not analytic_account_id and analytic_account_code:
                    error_analytic_account_not_exists.append(index + 1)
                if (debit_acc_id.x_required_product or credit_acc_id.x_required_product) and not product_code:
                    error_product_empty.append(index + 1)
                if (debit_acc_id.x_required_analytic or credit_acc_id.x_required_analytic) and not analytic_account_code:
                    error_analytic_account_empty.append(index + 1)
                if (debit_acc_id.x_required_expense_item or credit_acc_id.x_required_expense_item) and not account_expense_item_code:
                    error_account_expense_empty.append(index + 1)

                debit_partner_code = sheet.cell(index, 3).value
                debit_partner_id = self.env['res.partner'].search([('ref', '=', debit_partner_code)], limit=1)
                # if not debit_partner_id and debit_partner_code:
                #     raise UserError(_('Debit Partner with code (%s) does not exists, line (%s)', debit_partner_code, index))

                credit_partner_code = sheet.cell(index, 4).value
                credit_partner_id = self.env['res.partner'].search([('ref', '=', credit_partner_code)], limit=1)
                # if not credit_partner_id and credit_partner_code:
                #     raise UserError(_('Credit Partner with code (%s) does not exists, line (%s)', credit_partner_id, index))

                value = sheet.cell(index, 7).value
                if value:
                    if not _is_number(value):
                        error_invalid_value.append(index + 1)
                    else:
                        if value <= 0:
                            error_value_greater.append(index + 1)
                else:
                    error_value_empty.append(index + 1)

                error = ""
                if error_name_empty:
                    error += (_('Name is empty, line (%s) \n')) % str(', '.join(str(v) for v in error_name_empty))
                if error_debit_account_empty:
                    error += (_('Debit Account is empty, line (%s) \n')) % str(', '.join(str(v) for v in error_debit_account_empty))
                if error_credit_account_empty:
                    error += (_('Credit Account is empty, line (%s) \n')) % str(', '.join(str(v) for v in error_credit_account_empty))
                if error_debit_account_not_exists:
                    error += (_('Debit Account does not exists, line (%s)\n')) % str(
                        ', '.join(str(v) for v in error_debit_account_not_exists))
                if error_credit_account_not_exists:
                    error += (_('Credit Account does not exists, line (%s)\n')) % str(
                        ', '.join(str(v) for v in error_credit_account_not_exists))
                if error_product_not_exists:
                    error += (_('Product does not exists, line (%s)\n')) % str(', '.join(str(v) for v in error_product_not_exists))
                if error_account_expense_not_exists:
                    error += (_('Account expense item does not exists, line (%s)\n')) % str(
                        ', '.join(str(v) for v in error_account_expense_not_exists))
                if error_product_empty:
                    error += (_('Product cannot empty because Debit Account or Credit Account is '
                              'Required Product, line (%s)\n')) % str(', '.join(str(v) for v in error_product_empty))
                if error_analytic_account_not_exists:
                    error += (_('Account analytic does not exists, line (%s)\n')) % str(
                        ', '.join(str(v) for v in error_analytic_account_not_exists))
                if error_account_expense_empty:
                    error += (_('Account expense item cannot empty because Debit Account or Credit Account is '
                              'Required Expense Item, line (%s)\n')) % str(', '.join(str(v) for v in error_account_expense_empty))
                if error_analytic_account_empty:
                    error += (_('Analytic Account cannot empty because Debit Account or Credit Account is '
                              'Required Analytic Account, line (%s)\n')) % str(', '.join(str(v) for v in error_analytic_account_empty))
                if error_invalid_value:
                    error += (_('Invalid value, line (%s)\n')) % str(', '.join(str(v) for v in error_invalid_value))
                if error_value_greater:
                    error += (_('Value must be greater than 0, line (%s)\n')) % str(', '.join(str(v) for v in error_value_greater))
                if error_value_empty:
                    error += (_('Value is empty, line (%s) \n')) % str(', '.join(str(v) for v in error_value_empty))

                # value_natural_currency = sheet.cell(index, 8).value
                # if value_natural_currency:
                #     if not _is_number(value_natural_currency):
                #         raise UserError(_('Invalid value natural currency, line (%s)', index))

                if name and not error:
                    line_obj = self.env['accountant.bill.line'].search(
                        [('name', '=', name), ('product_id', '=', product_id.id),
                         ('account_expense_item_id', '=', account_expense_item_id.id),('accountant_bill_id','=',self.id),
                         ('debit_partner_id', '=', debit_partner_id.id), ('credit_partner_id', '=', credit_partner_id.id),
                         ('debit_acc_id', '=', debit_acc_id.id), ('credit_acc_id', '=', credit_acc_id.id),
                         ('analytic_account_id', '=', analytic_account_id.id)], limit=1)
                    if not line_obj:
                        move_vals = {
                            'accountant_bill_id': self.id,
                            'name': name,
                            'debit_acc_id': debit_acc_id.id,
                            'credit_acc_id': credit_acc_id.id,
                            'value': value,
                            # 'value_natural_currency': value_natural_currency,
                        }
                        if product_id:
                            move_vals['product_id'] = product_id.id
                        if account_expense_item_id:
                            move_vals['account_expense_item_id'] = account_expense_item_id.id
                        if debit_partner_id:
                            move_vals['debit_partner_id'] = debit_partner_id.id
                        if credit_partner_id:
                            move_vals['credit_partner_id'] = credit_partner_id.id
                        if analytic_account_id:
                            move_vals['analytic_account_id'] = analytic_account_id.id
                        line_id = self.env['accountant.bill.line'].create(move_vals)
                    else:
                        move_vals = {'value': line_obj.value + value}
                        line_id = line_obj.write(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
            if error:
                raise UserError(error)
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))


class AccountantBillLine(models.Model):
    _name = 'accountant.bill.line'

    accountant_bill_id = fields.Many2one('accountant.bill', ondelete='cascade')
    name = fields.Char('Description')
    product_id = fields.Many2one('product.product', string='Product')
    debit_acc_id = fields.Many2one('account.account', string="Debit Account")
    credit_acc_id = fields.Many2one('account.account', string="Credit Account")
    debit_partner_id = fields.Many2one('res.partner', string="Debit Partner")
    credit_partner_id = fields.Many2one('res.partner', string="Credit Partner")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    value = fields.Monetary(default=0.0, currency_field='currency_id', string="Value")
    value_natural_currency = fields.Float('Value natural currency')
    rate = fields.Float('Rate')
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_expense_item_id = fields.Many2one('account.expense.item', 'Account Expense Item')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure')

    debit_acc_required_product = fields.Boolean(related='debit_acc_id.x_required_product')
    debit_acc_required_analytic = fields.Boolean(related='debit_acc_id.x_required_analytic')
    debit_acc_required_expense_item = fields.Boolean(related='debit_acc_id.x_required_expense_item')
    credit_acc_required_product = fields.Boolean(related='credit_acc_id.x_required_product')
    credit_acc_required_analytic = fields.Boolean(related='credit_acc_id.x_required_analytic')
    credit_acc_required_expense_item = fields.Boolean(related='credit_acc_id.x_required_expense_item')

    @api.onchange('value')
    def onchange_value(self):
        if self.value:
            if self.rate and self.rate != 0:
                self.value_natural_currency = self.value * self.rate
            else:
                self.value_natural_currency = self.value

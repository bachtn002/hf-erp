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


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('x_amount_tax', 'x_amount_before_tax')
    def _amount_all(self):
        for order in self:
            amount = 0.0
            amount = order.x_amount_before_tax + order.x_amount_tax
            order.update({
                'x_amount': order.currency_id.round(amount),
            })

    @api.depends('cost_lines.value')
    def _amount_cost(self):
        for order in self:
            amount = 0.0
            for line in order.cost_lines:
                amount += line.value
            order.update({
                'x_amount_cost': order.currency_id.round(amount),
            })

    @api.depends('payment_lines.value')
    def _amount_before_tax(self):
        for order in self:
            amount = 0.0
            for line in order.payment_lines:
                amount += line.value
            order.update({
                'x_amount_before_tax': order.currency_id.round(amount),
            })

    @api.depends('tax_lines.amount_tax')
    def _amount_tax(self):
        for order in self:
            amount = 0.0
            for line in order.tax_lines:
                amount += line.amount_tax
            order.update({
                'x_amount_tax': order.currency_id.round(amount),
            })

    name = fields.Char(default=lambda self: _('New'), readonly=True, copy=False)
    x_name = fields.Char(default=lambda self: _('New'), copy=False)
    x_is_payment_vendor_cash = fields.Boolean('Payment Vendor Cash')
    x_is_payment_customer_cash = fields.Boolean('Payment Customer Cash')
    x_is_payment_customer_bank = fields.Boolean('Payment Customer Bank')
    x_is_payment_vendor_bank = fields.Boolean('Payment Vendor Bank')
    x_is_cash_expense = fields.Boolean('Cash Expense')
    x_is_bank_expense = fields.Boolean('Bank Expense')
    x_is_cash_in = fields.Boolean('Cash In')
    x_is_bank_in = fields.Boolean('Bank In')
    x_receiver = fields.Char('Receiver')
    x_date = fields.Date('Date', default=lambda self: fields.Date.today())
    x_address = fields.Char('Address')
    product_id = fields.Many2one('product.product', string='Expense')
    x_description = fields.Char('Description')
    payment_lines = fields.One2many('account.payment.line', 'payment_id', 'Payment Lines', copy=True)
    cost_lines = fields.One2many('account.payment.cost', 'payment_id', 'Cost Lines')
    general_lines = fields.One2many('account.payment.general', 'payment_id', 'General Lines')
    x_journal_id = fields.Many2one('account.journal', 'Account Journal')
    x_move_ids = fields.One2many('account.move', 'x_account_payment_id', string="Account Moves",
                                 track_visibility='always')
    x_total_entries = fields.Integer(string="Total Entries", compute="_compute_total_entry", track_visibility='always')
    x_bank_id = fields.Many2one('res.bank', 'Bank')
    x_code = fields.Char('Code')
    tax_lines = fields.One2many('account.payment.tax', 'payment_id', 'Tax Lines', copy=True)
    # amount = fields.Monetary(string='Payment Amount', required=True, store=True, compute='_amount_all')
    x_amount_before_tax = fields.Monetary(string='Payment Amount before tax', store=True, compute='_amount_before_tax')
    x_amount = fields.Monetary(string='Payment Amount', store=True, compute='_amount_all')
    x_amount_tax = fields.Monetary(string='Payment Amount Tax', store=True, compute='_amount_tax')
    x_partner_bank_id = fields.Many2one('res.partner.bank', 'Partner bank',domain="[('partner_id', '=', x_partner_id)]")
    tax_code = fields.Char('Tax Code')
    x_partner_id = fields.Many2one('res.partner', 'Partner')
    x_amount_cost = fields.Monetary(string='Amount cost', store=True, compute='_amount_cost')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    field_binary_import_cost = fields.Binary(string="Field Binary Import")
    field_binary_name_cost = fields.Char(string="Field Binary Name")
    x_rate = fields.Float('Rate')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    x_allocation_type = fields.Selection([('auto', 'Automatic'), ('manual', 'Manual')], default='auto',
                                         string='Allocation Type')
    x_payment_type = fields.Selection([('deposit', 'Deposit'), ('pay', 'Pay')], default='pay', string='Payment Type')
    x_account_default = fields.Many2one('account.account', 'Default account')

    def get_acc_number(self):
        company = self.company_id
        count = 0
        bank_acc_number = ""
        for bank in company.bank_ids:
            if bank.bank_id.bic == self.x_partner_bank_id.bank_id.bic:
                count += 1
                bank_acc_number = str(bank.acc_number)
                break
        if count == 0:
            for bank in company.bank_ids:
                bank_acc_number = str(bank.acc_number)
                break
        return bank_acc_number

    def get_acc_number_company(self):
        company = self.company_id
        count = 0
        bank_acc_number = ""
        for bank in company.partner_id.bank_ids:
            if bank.bank_id.bic == self.x_bank_id.bic:
                count += 1
                bank_acc_number = str(bank.acc_number)
                break
        if count == 0:
            for bank in company.partner_id.bank_ids:
                bank_acc_number = str(bank.acc_number)
                break
        return bank_acc_number

    @api.onchange('x_partner_id')
    def onchange_x_partner_id(self):
        if self.x_partner_id:

            if self.x_is_bank_expense:
                self.x_account_default = self.x_partner_id.property_account_payable_id.id
            elif self.x_is_bank_in:
                self.x_account_default = self.x_partner_id.property_account_receivable_id.id

            if self.x_is_cash_expense:
                self.x_account_default = self.x_partner_id.property_account_payable_id.id
            elif self.x_is_cash_in:
                self.x_account_default = self.x_partner_id.property_account_receivable_id.id
        else:
            self.x_account_default = ()

    @api.onchange('x_bank_id')
    def onchange_x_bank_id(self):
        if self.x_bank_id:
            self.x_journal_id = self.env['account.journal'].search([('bank_id', '=', self.x_bank_id.bic)], limit=1)
        # else:
        #     self.x_journal_id = ()

    @api.onchange('x_journal_id')
    def onchange_x_journal_id(self):
        if self.x_journal_id.id and self.x_bank_id.id == False:
            self.x_bank_id = self.x_journal_id.bank_id
        # else:
        #     self.x_bank_id = ()

    def get_acc_number2(self):
        bank_id = self.x_bank_id
        bank = self.env['account.journal'].search([('bank_id', '=', bank_id.id)], limit=1)
        return bank

    def get_account_credit(self):
        for l in self.payment_lines:
            credit = l.account_id.code
            break
        return credit

    def get_account_debt(self):
        for l in self.payment_lines:
            debt = l.destination_account_id.code
            break
        return debt

    @api.onchange('currency_id')
    def onchange_currency(self):
        if self.currency_id:
            self.x_rate = self.currency_id.x_rate
            for line in self.payment_lines:
                line.currency_id = self.currency_id
                line.rate = self.x_rate
                line.value_natural_currency = line.value * line.rate
            for cost_line in self.cost_lines:
                cost_line.currency_id = self.currency_id

    @api.onchange('x_rate')
    def onchange_rate(self):
        if self.x_rate:
            for line in self.payment_lines:
                line.rate = self.x_rate
                line.value_natural_currency = line.value * line.rate

    def write(self, vals):
        if 'x_name' in vals.keys():
            self.name = vals.get('x_name')
            move_id = self.env['account.move'].search([('x_account_payment_id', '=', self.id)], limit=1)
            if move_id:
                move_id.name = vals.get('x_name')
                for line in move_id.line_ids:
                    line.ref = vals.get('x_name')
        return super(AccountPayment, self).write(vals)

    @api.onchange('x_partner_id')
    def onchange_partner(self):
        if self.x_partner_id:
            self.partner_id = self.x_partner_id
            partner_bank = self.env['res.partner.bank'].search([('partner_id', '=', self.x_partner_id.id)], order='id',
                                                               limit=1)
            if partner_bank:
                self.x_partner_bank_id = partner_bank
            else:
                self.x_partner_bank_id = ()
            self.tax_code = self.x_partner_id.vat
            self.x_receiver = self.x_partner_id.x_legal_representation
            self.x_address = self.x_partner_id.street
            ids = []
            for id in self.x_partner_id.bank_ids:
                ids.append(id.id)
            return {
                'domain': {
                    'x_partner_bank_id': [('id', 'in', ids)]
                }
            }

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.x_code = self.product_id.property_account_expense_id.code

    @api.onchange('x_journal_id')
    def onchange_journal_default(self):
        if not self.x_journal_id.id:
            context = self._context
            if 'default_x_is_cash_expense' in context.keys():
                if context.get('default_x_is_cash_expense') == True:
                    journal_id = self.env['account.journal'].search([('code', '=', 'PC')], limit=1)
                    if journal_id:
                        self.x_journal_id = journal_id.id
            elif 'default_x_is_bank_expense' in context.keys():
                if context.get('default_x_is_bank_expense') == True:
                    journal_id = self.env['account.journal'].search([('code', '=', 'UNC')], limit=1)
                    if journal_id:
                        self.x_journal_id = journal_id.id
            elif 'default_x_is_cash_in' in context.keys():
                if context.get('default_x_is_cash_in') == True:
                    journal_id = self.env['account.journal'].search([('code', '=', 'PT')], limit=1)
                    if journal_id:
                        self.x_journal_id = journal_id.id
            elif 'default_x_is_bank_in' in context.keys():
                if context.get('default_x_is_bank_in') == True:
                    journal_id = self.env['account.journal'].search([('code', '=', 'NTTK')], limit=1)
                    if journal_id:
                        self.x_journal_id = journal_id.id

    def action_print(self):
        if self.x_is_cash_expense:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_account_cash_management/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        if self.x_is_cash_in:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_account_cash_management_receipts/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }

    def action_print_unc(self):
        if self.x_bank_id.bic == 'VCB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_VietComBank_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'AGR':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_agribank_view2/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'BIDV':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_bidv_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'VTB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_vietinbank_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }


    def action_view_move(self):
        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        result['domain'] = "[('id', 'in', " + str(self.x_move_ids.ids) + ")]"
        return result

    def _compute_total_entry(self):
        for record in self:
            move_ids = self.env['account.move'].search([('x_account_payment_id', '=', record.id)])
            record.x_total_entries = len(move_ids)

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.x_description = self.product_id.name

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        context = self._context
        if 'default_x_is_cash_expense' in context.keys() or 'default_x_is_payment_vendor_cash' in context.keys():
            if context.get('default_x_is_cash_expense') == True or context.get(
                    'default_x_is_payment_vendor_cash') == True:
                if vals_list[0].get('name', _('New')) == _('New'):
                    vals_list[0]['name'] = self.env['ir.sequence'].next_by_code('cash.expense') or _('New')
                    vals_list[0]['x_name'] = vals_list[0].get('name')
        elif 'default_x_is_bank_expense' in context.keys() or 'default_x_is_payment_vendor_bank' in context.keys():
            if context.get('default_x_is_bank_expense') == True or context.get(
                    'default_x_is_payment_vendor_bank') == True:
                if vals_list[0].get('name', _('New')) == _('New'):
                    vals_list[0]['name'] = self.env['ir.sequence'].next_by_code('bank.expense') or _('New')
                    vals_list[0]['x_name'] = vals_list[0].get('name')
        elif 'default_x_is_cash_in' in context.keys() or 'default_x_is_payment_customer_cash' in context.keys():
            if context.get('default_x_is_cash_in') == True or context.get('default_x_is_payment_customer_cash') == True:
                if vals_list[0].get('name', _('New')) == _('New'):
                    vals_list[0]['name'] = self.env['ir.sequence'].next_by_code('cash.in') or _('New')
                    vals_list[0]['x_name'] = vals_list[0].get('name')
        elif 'default_x_is_bank_in' in context.keys() or 'default_x_is_payment_customer_bank' in context.keys():
            if context.get('default_x_is_bank_in') == True or context.get('default_x_is_payment_customer_bank') == True:
                if vals_list[0].get('name', _('New')) == _('New'):
                    vals_list[0]['name'] = self.env['ir.sequence'].next_by_code('bank.in') or _('New')
                    vals_list[0]['x_name'] = vals_list[0].get('name')
        amount_total = 0.0
        if not vals_list[0].get('journal_id'):
            vals_list[0]['journal_id'] = vals_list[0].get('x_journal_id')
        if not vals_list[0].get('partner_id'):
            vals_list[0]['partner_id'] = vals_list[0].get('x_partner_id')
        if not vals_list[0].get('amount'):
            if 'payment_lines' in vals_list[0]:
                for line in vals_list[0].get('payment_lines'):
                    amount_total += line[2]['value']
            vals_list[0]['amount'] = amount_total
            vals_list[0]['x_amount'] = amount_total
        if not vals_list[0].get('x_amount'):
            vals_list[0]['x_amount'] = vals_list[0].get('amount')
        if not vals_list[0].get('amount') and not vals_list[0].get('x_amount'):
            vals_list[0]['x_amount'] = 0.0
        write_off_line_vals_list = []

        for vals in vals_list:

            # Hack to add a custom write-off line.
            write_off_line_vals_list.append(vals.pop('write_off_line_vals', None))

            # Force the move_type to avoid inconsistency with residual 'default_move_type' inside the context.
            vals['move_type'] = 'entry'

            # Force the computation of 'journal_id' since this field is set on account.move but must have the
            # bank/cash type.
            if 'journal_id' not in vals:
                vals['journal_id'] = self._get_default_journal().id

            # Since 'currency_id' is a computed editable field, it will be computed later.
            # Prevent the account.move to call the _get_default_currency method that could raise
            # the 'Please define an accounting miscellaneous journal in your company' error.
            if 'currency_id' not in vals:
                journal = self.env['account.journal'].browse(vals['journal_id'])
                vals['currency_id'] = journal.currency_id.id or journal.company_id.currency_id.id

        payments = super().create(vals_list)

        #check neu la chuc nang thanh toan custom, bo qua doan tao but toan mac dinh
        if 'default_x_is_bank_in' in context.keys() or 'default_x_is_payment_customer_bank' in context.keys() or \
            'default_x_is_cash_in' in context.keys() or 'default_x_is_payment_customer_cash' in context.keys() or \
            'default_x_is_cash_expense' in context.keys() or 'default_x_is_payment_vendor_cash' in context.keys() or \
            'default_x_is_bank_expense' in context.keys() or 'default_x_is_payment_vendor_bank' in context.keys():
            return payments
        else:
            for i, pay in enumerate(payments):
                write_off_line_vals = write_off_line_vals_list[i]

                # Write payment_id on the journal entry plus the fields being stored in both models but having the same
                # name, e.g. partner_bank_id. The ORM is currently not able to perform such synchronization and make things
                # more difficult by creating related fields on the fly to handle the _inherits.
                # Then, when partner_bank_id is in vals, the key is consumed by account.payment but is never written on
                # account.move.
                to_write = {'payment_id': pay.id}
                for k, v in vals_list[i].items():
                    if k in self._fields and self._fields[k].store and k in pay.move_id._fields and pay.move_id._fields[k].store:
                        to_write[k] = v

                if 'line_ids' not in vals_list[i]:
                    to_write['line_ids'] = [(0, 0, line_vals) for line_vals in
                                            pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)]

                pay.move_id.write(to_write)

        return payments

    def write(self, vals):
        # OVERRIDE
        res = super().write(vals)
        if self.x_is_payment_vendor_cash == True or self.x_is_payment_customer_cash == True or \
            self.x_is_payment_vendor_bank == True or self.x_is_payment_customer_bank == True or \
            self.x_is_cash_expense == True or self.x_is_bank_expense == True or \
            self.x_is_cash_in == True or self.x_is_bank_in:
            return res
        else:
            self._synchronize_to_moves(set(vals.keys()))
            return res

    # @api.model
    # def create(self, values):
    #     context = self._context
    #     if 'default_x_is_cash_expense' in context.keys() or 'default_x_is_payment_vendor_cash' in context.keys():
    #         if context.get('default_x_is_cash_expense') == True or context.get(
    #                 'default_x_is_payment_vendor_cash') == True:
    #             if values.get('name', _('New')) == _('New'):
    #                 values['name'] = self.env['ir.sequence'].next_by_code('cash.expense') or _('New')
    #                 values['x_name'] = values.get('name')
    #     elif 'default_x_is_bank_expense' in context.keys() or 'default_x_is_payment_vendor_bank' in context.keys():
    #         if context.get('default_x_is_bank_expense') == True or context.get(
    #                 'default_x_is_payment_vendor_bank') == True:
    #             if values.get('name', _('New')) == _('New'):
    #                 values['name'] = self.env['ir.sequence'].next_by_code('bank.expense') or _('New')
    #                 values['x_name'] = values.get('name')
    #     elif 'default_x_is_cash_in' in context.keys() or 'default_x_is_payment_customer_cash' in context.keys():
    #         if context.get('default_x_is_cash_in') == True or context.get('default_x_is_payment_customer_cash') == True:
    #             if values.get('name', _('New')) == _('New'):
    #                 values['name'] = self.env['ir.sequence'].next_by_code('cash.in') or _('New')
    #                 values['x_name'] = values.get('name')
    #     elif 'default_x_is_bank_in' in context.keys() or 'default_x_is_payment_customer_bank' in context.keys():
    #         if context.get('default_x_is_bank_in') == True or context.get('default_x_is_payment_customer_bank') == True:
    #             if values.get('name', _('New')) == _('New'):
    #                 values['name'] = self.env['ir.sequence'].next_by_code('bank.in') or _('New')
    #                 values['x_name'] = values.get('name')
    #     amount_total = 0.0
    #     if not values.get('journal_id'):
    #         values['journal_id'] = values.get('x_journal_id')
    #     if not values.get('partner_id'):
    #         values['partner_id'] = values.get('x_partner_id')
    #     if not values.get('amount'):
    #         if 'payment_lines' in values:
    #             for line in values.get('payment_lines'):
    #                 amount_total += line[2]['value']
    #         values['amount'] = amount_total
    #         values['x_amount'] = amount_total
    #     if not values.get('x_amount'):
    #         values['x_amount'] = values.get('amount')
    #     if not values.get('amount') and not values.get('x_amount'):
    #         values['x_amount'] = 0.0
    #     return super(AccountPayment, self).create(values)

    def _general_payment(self):
        for line in self.payment_lines:
            credit_general_id = self.env['account.payment.general'].search(
                [('payment_id', '=', self.id), ('account_id', '=', line.account_id.id)], limit=1)
            debit_general_id = self.env['account.payment.general'].search(
                [('payment_id', '=', self.id), ('destination_account_id', '=', line.destination_account_id.id)],
                limit=1)
            if credit_general_id:
                credit_general_id.value_credit += line.value_natural_currency if line.value_natural_currency != 0 else line.value
            else:
                self.env['account.payment.general'].create({
                    'payment_id': self.id,
                    'account_id': line.account_id.id,
                    'value_credit': line.value_natural_currency if line.value_natural_currency != 0 else line.value
                })
            if debit_general_id:
                debit_general_id.value_debit += line.value_natural_currency if line.value_natural_currency != 0 else line.value
            else:
                self.env['account.payment.general'].create({
                    'payment_id': self.id,
                    'destination_account_id': line.destination_account_id.id,
                    'value_debit': line.value_natural_currency if line.value_natural_currency != 0 else line.value
                })
        payment_line_id = self.env['account.payment.line'].search([('payment_id', '=', self.id)], limit=1)
        for line_tax in self.tax_lines:
            credit_general_id = self.env['account.payment.general'].search(
                [('payment_id', '=', self.id), ('account_id', '=', payment_line_id.account_id.id)], limit=1)
            debit_general_id = self.env['account.payment.general'].search(
                [('payment_id', '=', self.id), ('destination_account_id', '=', line_tax.account_tax_id.id)],
                limit=1)
            if credit_general_id:
                credit_general_id.value_credit += line_tax.amount_tax
            else:
                self.env['account.payment.general'].create({
                    'payment_id': self.id,
                    'account_id': payment_line_id.account_id.id,
                    'value_credit': line_tax.amount_tax
                })
            if debit_general_id:
                debit_general_id.value_debit += line_tax.amount_tax
            else:
                self.env['account.payment.general'].create({
                    'payment_id': self.id,
                    'destination_account_id': line_tax.account_tax_id.id,
                    'value_debit': line_tax.amount_tax
                })
        for line_cost in self.cost_lines:
            credit_general_id = self.env['account.payment.general'].search(
                [('payment_id', '=', self.id), ('account_id', '=', line_cost.account_id.id)], limit=1)
            debit_general_id = self.env['account.payment.general'].search(
                [('payment_id', '=', self.id), ('destination_account_id', '=', line_cost.destination_account_id.id)],
                limit=1)
            if credit_general_id:
                credit_general_id.value_credit += line_cost.value
            else:
                self.env['account.payment.general'].create({
                    'payment_id': self.id,
                    'account_id': line_cost.account_id.id,
                    'value_credit': line_cost.value
                })
            if debit_general_id:
                debit_general_id.value_debit += line_cost.value
            else:
                self.env['account.payment.general'].create({
                    'payment_id': self.id,
                    'destination_account_id': line_cost.destination_account_id.id,
                    'value_debit': line_cost.value
                })

    def action_confirm(self):
        self.ensure_one()
        if self.move_id:
            sql="""
            Delete from account_move where id = %s;
            """
            self._cr.execute(sql % (self.move_id.id))
        self.amount = self.x_amount
        if self.state == 'posted':
            raise UserError("Record has been posted! Refresh your browser, please")
        if len(self.payment_lines) == 0:
            raise UserError("You do not have accounting details, please check again!")
        amount_total = 0.0
        for line in self.payment_lines:
            amount_total += line.value
        self.amount = amount_total
        self._general_payment()
        if self.x_partner_id:
            self.partner_id = self.x_partner_id
            if self.x_is_bank_expense or self.x_is_cash_expense:
                if self.x_partner_id.property_account_payable_id.id == self.product_id.property_account_expense_id.id:
                    payment_line_id = self.env['account.payment.line'].search([('payment_id', '=', self.id)], limit=1)
                    journal_id = self.env['account.journal'].search(
                        [('default_debit_account_id', '=', payment_line_id.account_id.id)], limit=1)
                    if journal_id:
                        self.journal_id = journal_id
                    else:
                        raise UserError("You have not configured the Account Journal, please check again!")
                    self.post()
                else:
                    self._action_post()
            else:
                if self.x_partner_id.property_account_receivable_id.id == self.product_id.property_account_income_id.id:
                    payment_line_id = self.env['account.payment.line'].search([('payment_id', '=', self.id)], limit=1)
                    journal_id = self.env['account.journal'].search(
                        [('default_credit_account_id', '=', payment_line_id.destination_account_id.id)], limit=1)
                    if journal_id:
                        self.journal_id = journal_id
                    else:
                        raise UserError("You have not configured the Account Journal, please check again!")
                    self.post()
                else:
                    self._action_post()
        else:
            self._action_post()
        if self.state == 'posted' and self.x_allocation_type == 'auto':
            if self.x_is_payment_vendor_bank == True or self.x_is_payment_vendor_cash == True:
                for move_id in self.x_move_ids:
                    move_line_debit = self.env['account.move.line'].search(
                        [('move_id', '=', move_id.id), ('debit', '>', 0),
                         ('parent_state', '=', 'posted'), ('account_internal_type', '=', 'payable'),
                         ('reconciled', '=', False),
                         ('amount_residual', '>', 0)], limit=1)
                    if move_line_debit:
                        account_invoice = self.env['account.move'].search([('partner_id', '=', self.x_partner_id.id),
                                                                           ('type', '=', 'in_invoice'),
                                                                           ('invoice_payment_state', '=', 'not_paid'),
                                                                           ('state', '=', 'posted')],
                                                                          order='invoice_date')
                        for invoice in account_invoice:
                            if move_line_debit.amount_residual > 0:
                                invoice.js_assign_outstanding_line(move_line_debit.id)
            elif self.x_is_payment_customer_bank == True or self.x_is_payment_customer_cash == True:
                for move_id in self.x_move_ids:
                    move_line_credit = self.env['account.move.line'].search(
                        [('move_id', '=', move_id.id), ('credit', '>', 0),
                         ('parent_state', '=', 'posted'), ('account_internal_type', '=', 'receivable'),
                         ('reconciled', '=', False), ('amount_residual', '<', 0)], limit=1)
                    if move_line_credit:
                        account_invoice = self.env['account.move'].search([('partner_id', '=', self.x_partner_id.id),
                                                                           ('type', '=', 'out_invoice'),
                                                                           ('invoice_payment_state', '=', 'not_paid'),
                                                                           ('state', '=', 'posted')],
                                                                          order='invoice_date')
                        for invoice in account_invoice:
                            if move_line_credit.amount_residual < 0:
                                invoice.js_assign_outstanding_line(move_line_credit.id)
        # elif  self.state == 'posted' and self.x_allocation_type == 'manual':
        if self.x_payment_type == 'deposit':
            for line in self.payment_lines:
                if line.purchase_order_id:
                    if line.purchase_order_id.x_status_deposit == False:
                        line.purchase_order_id.x_deposit_amount += line.value_natural_currency
                        line.purchase_order_id.x_remaining_amount += line.value_natural_currency
                        line.purchase_order_id.x_status_deposit = 'deposit'
                    else:
                        line.purchase_order_id.x_deposit_amount += line.value_natural_currency
                        line.purchase_order_id.x_remaining_amount += line.value_natural_currency

    def _action_post(self):
        move_lines = []
        amount = 0
        for line in self.payment_lines:
            if line.value <= 0:
                raise UserError("Total amount must be greater than 0")
            line.currency_id = self.currency_id
            # Ghi sổ trả/nhận của các đối tác
            debit_move_vals = {
                'name': line.name,
                'ref': self.name,
                'date': self.date,
                'account_id': line.destination_account_id.id,
                'debit': line.value_natural_currency if line.value_natural_currency != 0 else line.value,
                'credit': 0.0,
                'partner_id': line.partner_id.id if line.partner_id else self.x_partner_id.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'x_accountant_payment_line_id': line.id
            }
            if line.currency_id.id != self.company_id.currency_id.id:
                debit_move_vals['currency_id'] = line.currency_id.id
                debit_move_vals['amount_currency'] = line.value
            if line.analytic_account_id.id:
                debit_move_vals['analytic_account_id'] = line.analytic_account_id.id
            if line.purchase_order_id:
                debit_move_vals['x_purchase_order_id'] = line.purchase_order_id.id
            move_lines.append((0, 0, debit_move_vals))

            # Ghi sổ thu/chi của công ty
            credit_move_vals = {
                'ref': self.name,
                'name': line.name,
                'date': self.date,
                'account_id': line.account_id.id,
                'debit': 0.0,
                'credit': line.value_natural_currency if line.value_natural_currency != 0 else line.value,
                'partner_id': self.x_partner_id.id,
                'x_accountant_payment_line_id': line.id
            }
            if line.currency_id.id != self.company_id.currency_id.id:
                credit_move_vals['currency_id'] = line.currency_id.id
                credit_move_vals['amount_currency'] = -line.value
            if line.analytic_account_id.id:
                credit_move_vals['analytic_account_id'] = line.analytic_account_id.id
            if line.purchase_order_id:
                credit_move_vals['x_purchase_order_id'] = line.purchase_order_id.id
            move_lines.append((0, 0, credit_move_vals))

        if len(self.tax_lines) > 0:
            payment_line_id = self.env['account.payment.line'].search([('payment_id', '=', self.id)], limit=1)
            amount = 0
            for tax in self.tax_lines:
                if tax.amount_tax > 0:
                    # Ghi sổ trả/nhận của các đối tác
                    debit_move_vals = {
                        'name': tax.name,
                        'ref': tax.name,
                        'date': self.date,
                        'account_id': tax.account_tax_id.id,
                        'debit': tax.amount_tax * self.x_rate,
                        'credit': 0.0,
                        'partner_id': tax.partner_id.id if tax.partner_id else self.x_partner_id.id,
                        'product_id': self.product_id.id,
                        'product_uom_id': self.product_id.uom_id.id,
                        'x_accountant_payment_tax_id': tax.id
                    }
                    move_lines.append((0, 0, debit_move_vals))

                    # Ghi sổ thu/chi của công ty
                    credit_move_vals = {
                        'ref': tax.name,
                        'name': tax.name,
                        'date': self.date,
                        'account_id': payment_line_id.account_id.id,
                        'debit': 0.0,
                        'credit': tax.amount_tax * self.x_rate,
                        'partner_id': tax.partner_id.id if tax.partner_id else self.x_partner_id.id,
                        'x_accountant_payment_tax_id': tax.id
                    }
                    move_lines.append((0, 0, credit_move_vals))
                elif tax.amount_tax < 0:
                    # Ghi sổ trả/nhận của các đối tác
                    debit_move_vals = {
                        'name': tax.name,
                        'ref': tax.name,
                        'date': self.date,
                        'account_id': payment_line_id.account_id.id,
                        'debit': tax.amount_tax * self.x_rate,
                        'credit': 0.0,
                        'partner_id': tax.partner_id.id if tax.partner_id else self.x_partner_id.id,
                        'product_id': self.product_id.id,
                        'product_uom_id': self.product_id.uom_id.id,
                        'x_accountant_payment_tax_id': tax.id
                    }
                    move_lines.append((0, 0, debit_move_vals))

                    # Ghi sổ thu/chi của công ty
                    credit_move_vals = {
                        'ref': tax.name,
                        'name': tax.name,
                        'date': self.date,
                        'account_id': tax.account_tax_id.id,
                        'debit': 0.0,
                        'credit': tax.amount_tax * self.x_rate,
                        'partner_id': tax.partner_id.id if tax.partner_id else self.x_partner_id.id,
                        'x_accountant_payment_tax_id': tax.id
                    }
                    move_lines.append((0, 0, credit_move_vals))
        if len(self.cost_lines) > 0:
            for cost_line in self.cost_lines:
                if cost_line.value <= 0:
                    raise UserError("Total amount must be greater than 0")
                cost_line.currency_id = self.currency_id

                # Ghi sổ trả/nhận của các đối tác
                debit_move_vals = {
                    'name': cost_line.name,
                    'ref': cost_line.name,
                    'date': self.date,
                    'account_id': cost_line.destination_account_id.id,
                    'debit': cost_line.value,
                    'credit': 0.0,
                }
                move_lines.append((0, 0, debit_move_vals))

                # Ghi sổ thu/chi của công ty
                credit_move_vals = {
                    'ref': cost_line.name,
                    'name': cost_line.name,
                    'date': self.date,
                    'account_id': cost_line.account_id.id,
                    'debit': 0.0,
                    'credit': cost_line.value,
                }
                move_lines.append((0, 0, credit_move_vals))

        move_vals = {
            'ref': self.name,
            'date': self.date,
            'journal_id': self.x_journal_id.id,
            'line_ids': move_lines,
            'x_account_payment_id': self.id,
            'name': self.name
        }
        if self.currency_id.id != self.company_id.currency_id.id:
            move_vals['currency_id'] = self.currency_id.id
            move_vals['x_rate'] = self.x_rate
        if self.x_partner_id:
            move_vals['partner_id'] = self.x_partner_id.id
        move_id = self.env['account.move'].create(move_vals)
        move_id.post()
        move_id.name = self.name
        self.write({'state': 'posted'})
        return True

    @api.model
    def get_amount_word(self):
        res = num2word(int(self.x_amount))
        if self.currency_id.name == 'VND':
            res += " đồng chẵn"
        return res

    @api.model
    def get_amount_to_word(self, amount):
        res = num2word(int(amount))
        res += ' đồng chẵn'
        return res

    @api.model
    def get_debit_credit_list(self):
        res = {'debit': {}, 'credit': {}}
        move_id = self.env['account.move'].search([('x_account_payment_id', '=', self.id)], limit=1)
        if move_id:
            for line in move_id.line_ids:
                if line.debit > 0:
                    res['debit'][line.account_id.code] = line.debit
                if line.credit > 0:
                    res['credit'][line.account_id.code] = line.credit
        return res

    def action_back(self):
        if self.state == 'posted':
            for line in self.payment_lines:
                if line.purchase_order_id:
                    if line.purchase_order_id.x_allocated_amount > 0:
                        raise UserError(_("You cannot return when contract allocated."))
                    else:
                        line.purchase_order_id.x_deposit_amount = 0
                        line.purchase_order_id.x_allocated_amount = 0
                        line.purchase_order_id.x_remaining_amount = 0
            #self.cancel()
            if len(self.general_lines) > 0:
                self.general_lines.unlink()
            if len(self.x_move_ids) > 0:
                move_ids = self.x_move_ids.with_context(force_delete=True)
                move_ids.button_cancel()
                move_ids.unlink()
            self.state = 'draft'

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

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
            lines = []
            while index < sheet.nrows:
                dest_account_code = sheet.cell(index, 1).value
                dest_account_code = str(int(dest_account_code)).upper()
                dest_account_id = self.env['account.account'].search([('code', '=', dest_account_code)], limit=1)
                if not dest_account_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại tài khoản có mã " + dest_account_code))
                account_code = sheet.cell(index, 2).value
                account_code = str(int(account_code)).upper()
                account_id = self.env['account.account'].search([('code', '=', account_code)], limit=1)
                if not account_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại tài khoản có mã " + account_code))
                value = sheet.cell(index, 3).value
                value_natural_currency = sheet.cell(index, 4).value
                name = sheet.cell(index, 5).value
                move_vals = {
                    'payment_id': self.id,
                    'name': name if name != '' else self.x_description,
                    'value': value,
                    'value_natural_currency': value_natural_currency if value_natural_currency != '' else value * self.x_rate,
                    'account_id': account_id.id,
                    'destination_account_id': dest_account_id.id,
                    'currency_id': self.currency_id.id,
                    'rate': self.x_rate
                }
                line_id = self.env['account.payment.line'].create(move_vals)
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def action_import_line_cost(self):
        try:
            if not self._check_format_excel(self.field_binary_name_cost):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import_cost)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 1
            lines = []
            while index < sheet.nrows:
                shop_code = sheet.cell(index, 0).value
                shop_code = shop_code.upper()
                analytic_account_id = self.env['account.analytic.account'].search([('code', '=', shop_code)], limit=1)
                if not analytic_account_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại shop có mã " + shop_code))
                dest_account_code = sheet.cell(index, 1).value
                dest_account_code = str(int(dest_account_code)).upper()
                dest_account_id = self.env['account.account'].search([('code', '=', dest_account_code)], limit=1)
                if not dest_account_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại tài khoản có mã " + dest_account_code))
                account_code = sheet.cell(index, 2).value
                account_code = str(int(account_code)).upper()
                account_id = self.env['account.account'].search([('code', '=', account_code)], limit=1)
                if not account_id:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại tài khoản có mã " + account_code))
                value = sheet.cell(index, 3).value
                value_natural_currency = sheet.cell(index, 4).value
                name = sheet.cell(index, 5).value
                if analytic_account_id:
                    move_vals = {
                        'payment_id': self.id,
                        'name': name if name != '' else self.x_description,
                        'value': value,
                        'account_id': account_id.id,
                        'destination_account_id': dest_account_id.id
                    }
                    line_id = self.env['account.payment.cost'].create(move_vals)
                index = index + 1
            self.field_binary_import_cost = None
            self.field_binary_name_cost = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_account_payment/static/template/import_account_payment.xlsx',
            "target": "_parent",
        }

    def unlink(self):
        if any(bool(rec.move_line_ids) for rec in self):
            raise UserError(_("You cannot delete a payment that is already posted."))
        if any(rec.move_name for rec in self):
            raise UserError(_(
                'It is not allowed to delete a payment that already created a journal entry since it would create a gap in the numbering. You should create the journal entry again and cancel it thanks to a regular revert.'))
        for line in self:
            if line.state not in ('draft', 'cancelled'):
                raise UserError(_('Bạn chỉ có thể xóa khi ở trạng thái Nháp'))
        return super(AccountPayment, self).unlink()

    def get_applicant(self):
        company = self.company_id
        return company

    def action_show_popup_print_unc(self):
        self.ensure_one()
        return {
            'name': _('Print UNC'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment.unc.wizard',
            'no_destroy': False,
            'target': 'new',
            'view_id': self.env.ref(
                'ev_account_payment.wizard_account_payment_vendor_unc_view_form') and self.env.ref(
                'ev_account_payment.wizard_account_payment_vendor_unc_view_form').id or False,
            'context': {'default_payment_id': self.id},
        }


class AccountPaymentLine(models.Model):
    _name = 'account.payment.line'

    payment_id = fields.Many2one('account.payment', 'Account Payment')
    name = fields.Char('Description')
    value = fields.Monetary('Value', required=True)
    value_natural_currency = fields.Float('Value natural currency')
    account_id = fields.Many2one('account.account', 'Account credit')
    destination_account_id = fields.Many2one('account.account', 'Destination account')
    partner_id = fields.Many2one('res.partner', 'Partner')
    currency_id = fields.Many2one('res.currency', string='Currency')
    date = fields.Date(related='payment_id.date', string='State of Asset', readonly=True, store=True)
    rate = fields.Float('Rate')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    origin = fields.Char('Contract')

    @api.onchange('value')
    def onchange_value(self):
        if self.value:
            if self.rate and self.rate != 0:
                self.value_natural_currency = self.value * self.rate
            else:
                self.value_natural_currency = self.value

    @api.onchange('payment_id')
    def onchange_payment(self):
        if self.payment_id:
            if 'default_x_is_cash_in' in self.payment_id._context:
                if self.payment_id._context['default_x_is_cash_in'] == True:
                    account_id = self.env['account.account'].search(
                        [('currency_id', '=', self.currency_id.x_base_currency_id.id)], limit=1)
                    if account_id:
                        self.destination_account_id = account_id
            if self.payment_id.x_partner_id:
                return {
                    'domain': {
                        'purchase_order_id': [('partner_id', '=', self.payment_id.x_partner_id.id),('state','not in',('draft','cancel'))]
                    }
                }

    @api.onchange('purchase_order_id')
    def onchange_purchase_order(self):
        if self.purchase_order_id:
            self.origin = self.purchase_order_id.origin
            if self.payment_id.x_payment_type == 'deposit':
                if self.purchase_order_id.payment_term_id:
                    payment_term_line_id = self.env['account.payment.term.line'].search([('payment_id','=',self.purchase_order_id.payment_term_id.id),
                                                                                         ('value','=','percent')], limit=1)
                    if payment_term_line_id:
                        self.value = payment_term_line_id.value_amount*self.purchase_order_id.amount_total/100
                if self.purchase_order_id.company_id.x_account_deposit_id:
                    self.destination_account_id = self.purchase_order_id.company_id.x_account_deposit_id
                else:
                    raise UserError(_("You have not configured a deposit account."))


class AccountPaymentTax(models.Model):
    _name = 'account.payment.tax'

    payment_id = fields.Many2one('account.payment', 'Account Payment')
    name = fields.Char('Description')
    account_tax_id = fields.Many2one('account.account', 'Account Tax')
    amount_tax = fields.Monetary('Amount tax')
    percent_tax = fields.Float('Percent Tax')
    amount_invoice = fields.Monetary('Amount invoice before tax')
    date_invoice = fields.Date('Date Invoice')
    code_invoice = fields.Char('Code Invoice')
    number_invoice = fields.Char('Number Invoice')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    currency_id = fields.Many2one('res.currency', string='Currency')
    number_invoice_form = fields.Char('Number Invoice Form')

    @api.onchange('amount_invoice', 'percent_tax')
    def onchange_amount_tax(self):
        if self.amount_invoice and self.percent_tax:
            self.amount_tax = (self.amount_invoice / 100) * self.percent_tax
        else:
            self.amount_tax = 0


class AccountPaymentCost(models.Model):
    _name = 'account.payment.cost'

    payment_id = fields.Many2one('account.payment', 'Account Payment')
    name = fields.Char('Description')
    value = fields.Monetary('Value', required=True)
    account_id = fields.Many2one('account.account', 'Account credit')
    destination_account_id = fields.Many2one('account.account', 'Destination account')
    currency_id = fields.Many2one('res.currency', string='Currency')
    date = fields.Date(related='payment_id.date', string='State of Asset', readonly=True, store=True)


class AccountPaymentGeneral(models.Model):
    _name = 'account.payment.general'

    payment_id = fields.Many2one('account.payment', 'Account Payment')
    account_id = fields.Many2one('account.account', 'Account credit')
    destination_account_id = fields.Many2one('account.account', 'Destination account')
    value_debit = fields.Float('Value debit')
    value_credit = fields.Float('Value credit')

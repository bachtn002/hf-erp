from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from dateutil.relativedelta import relativedelta

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


class LoanBorrowOrderPrintUNCWizard(models.TransientModel):
    _name = 'loan.borrowing.order.unc'
    _description = 'Print UNC'

    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    disbursement_id = fields.Many2one('loan.borrow.disbursement', 'Disbursement')
    x_bank_id = fields.Many2one('res.bank', 'Bank')

    @api.onchange('disbursement_id')
    def _onchange_disbursement_id_domain_partner_id(self):
        partner_ids_list = []
        if self.disbursement_id.purchase_order_ids or self.disbursement_id.invoice_ids:
            for line in self.disbursement_id.purchase_order_ids:
                if line.partner_id.id not in partner_ids_list:
                    partner_ids_list.append(line.partner_id.id)
            for inv in self.disbursement_id.invoice_ids:
                if inv.partner_id.id not in partner_ids_list:
                    partner_ids_list.append(inv.partner_id.id)

            if partner_ids_list:
                return {'domain': {
                    'partner_id': [('id', 'in', partner_ids_list), '|', ('company_id', '=', False),
                                   ('company_id', '=', self.disbursement_id.company_id.id)]}}
        else:
            return {'domain': {
                'partner_id': [('id', 'in', []), '|', ('company_id', '=', False),
                               ('company_id', '=', self.disbursement_id.company_id.id)]}}

    def get_account_number_credit(self):
        credit_acc_number = ""
        for line in self.partner_id.bank_ids:
            if line.acc_number:
                credit_acc_number = line.acc_number
            break
        return credit_acc_number

    def get_account_name_credit(self):
        credit_acc_name = self.partner_id.name
        return credit_acc_name

    def get_with_bank_credit(self):
        credit_with_bank = ""
        for line in self.partner_id.bank_ids:
            if line.bank_id:
                credit_with_bank = line.bank_id.name
            break
        return credit_with_bank

    def get_account_number_debit(self):
        debit_acc_number = ""
        for line in self.disbursement_id.order_id.partner_id.bank_ids:
            if line.acc_number:
                debit_acc_number = line.acc_number
            break
        return debit_acc_number

    def get_account_name_debit(self):
        debit_acc_name = self.disbursement_id.partner_id.name
        return debit_acc_name

    def get_address_credit(self):
        credit_acc_address = self.partner_id.street
        return credit_acc_address

    def get_amount(self):
        total_amount = 0.0
        order_id = self.disbursement_id.order_id.id
        disbursement_name = self.disbursement_id.name
        disbursement_payment_match_ids = self.env['loan.borrow.disbursement.payment.match'].search(
            [('order_id', '=', order_id), ('payment_id.name', '=', disbursement_name), ('payment_state', '=', 'posted')])
        partner_id = self.partner_id
        for line in disbursement_payment_match_ids:
            for item_invoice in line.payment_id.invoice_ids:
                if item_invoice.partner_id == partner_id:
                    total_amount += line.matched_amount

            for item_po in line.payment_id.purchase_order_ids:
                if item_po.partner_id == partner_id:
                    total_amount += line.matched_amount
        return total_amount

    def get_name_debit(self):
        name = self.disbursement_id.company_id.name
        return name

    @api.model
    def get_amount_to_word(self, amount):
        res = num2word(int(amount))
        if self.disbursement_id.currency_id.name:
            res += ' ' + self.disbursement_id.currency_id.name.lower()
        return res

    def action_print_unc(self):
        if self.x_bank_id.bic == 'VCB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/to_loan_management.report_unc_VietComBank_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'BIDV':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/to_loan_management.report_bidv_loan_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'VTB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/to_loan_management.report_vietinbank_loan_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }

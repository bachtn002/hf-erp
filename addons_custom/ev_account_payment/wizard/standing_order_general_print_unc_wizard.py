from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
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


class StandingOrderGeneralUNCWizard(models.TransientModel):
    _name = 'standing.order.general.unc'
    _description = 'Print UNC'
    _rec_name = 'general_id'

    general_id = fields.Many2one('standing.order.general', 'General')
    x_bank_id = fields.Many2one('res.bank', 'Bank')

    def _get_bank_acc_number(self):
        company = self.general_id.company_id.partner_id.bank_ids
        bank_acc_number = ""
        for item in company:
            if item.bank_id.bic == self.x_bank_id.bic:
                bank_acc_number = item.acc_number
                break
        return bank_acc_number

    def _get_bank_acc_number_beneficiary(self):
        move_vals = ""
        if self.general_id.lines:
            for item in self.general_id.lines:
                if item.partner_bank_id:
                    move_vals = str(item.partner_bank_id.acc_number)
                    break
        return move_vals

    def _get_bank_acc_name_beneficiary(self):
        move_vals = ""
        if self.general_id.lines:
            for item in self.general_id.lines:
                if item.partner_bank_id:
                    move_vals = str(item.partner_bank_id.bank_id.name)
                    break
        return move_vals

    def _get_partner_bank(self):
        branch_bank = ""
        if self.general_id:
            if self.general_id.journal_id:
                if self.general_id.journal_id.bank_account_id:
                    branch_bank = self.general_id.journal_id.bank_account_id.x_branch_bank
        return branch_bank

    def _get_partner(self):
        name_bank = ""
        if self.general_id:
            if self.general_id.journal_id:
                if self.general_id.journal_id.bank_account_id:
                    name_bank = self.general_id.journal_id.bank_account_id.bank_id.name
        return name_bank

    @api.model
    def _get_amount_to_word(self, amount):
        res = num2word(int(amount))
        if self.general_id.currency_id.name:
            res += ' ' + self.general_id.currency_id.name.lower()
        return res

    def action_print_unc(self):
        if self.x_bank_id.bic == 'VCB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_vcb_unc_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'BIDV':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_bidv_unc_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'VTB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.report_vietinbank_unc_template/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }

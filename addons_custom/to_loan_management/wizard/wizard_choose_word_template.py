from odoo import models, fields, api, _
from io import BytesIO
from tempfile import NamedTemporaryFile
# from docxtpl import DocxTemplate, Listing
import codecs
from odoo.exceptions import ValidationError


def convert_date(date_cv):
    if date_cv:
        return str(date_cv.day) + '/' + str(date_cv.month) + '/' + str(date_cv.year)
    else:
        return ""


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


def check(data):
    if data:
        return data
    else:
        return ""


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


class WizardChooseWordTemplate(models.TransientModel):
    _name = 'wizard.choose.word.template'
    _description = 'Print'

    word_template_id = fields.Many2one('word.template', 'Word Template', required=True)
    refund_payment_id = fields.Many2one('loan.borrow.refund.payment.match', 'Refund payment')
    file_name = fields.Char(string='File name')

    def get_amount(self, disbursement_payment_match_id, partner_id):
        total_amount = 0.0
        for item_po in disbursement_payment_match_id.payment_id.purchase_order_ids:
            if item_po.partner_id.id == partner_id:
                total_amount += disbursement_payment_match_id.payment_id.matched_amount
        return total_amount

    def get_amount_usd(self, disbursement_payment_match_id):
        total_amount = 0.0
        for item in disbursement_payment_match_id.payment_id.move_id.journal_general_ids:
            if item.amount_currency:
                total_amount += item.amount_currency
        return total_amount

    def get_amount_vnd(self, disbursement_payment_match_id):
        total_amount = 0.0
        for item in disbursement_payment_match_id.payment_id.move_id.journal_general_ids:
            if item.value:
                total_amount += item.value
        return total_amount

    def get_currency_name(self, disbursement_payment_match_id):
        currency_name = ""
        for item in disbursement_payment_match_id.payment_id.move_id.journal_general_ids:
            if item.currency_id:
                currency_name += item.currency_id.name
        return currency_name

    def get_contract_code(self, disbursement_payment_match_id):
        contract_code = ""
        for item in disbursement_payment_match_id.payment_id.move_id.journal_general_ids:
            if item.name:
                contract_code = item.name
        return contract_code

    def get_contract_date(self, disbursement_payment_match_id):
        contract_date = ""
        for item in disbursement_payment_match_id.payment_id.move_id.journal_general_ids:
            if item.date:
                contract_date = str(convert_date(item.date))
        return contract_date

    def get_account_number_partner(self, partner_id):
        acc_number = ""
        for line in partner_id.bank_ids:
            if line.acc_number:
                acc_number = line.acc_number
                break
        return acc_number.strip()

    def get_bank_name_partner(self, partner_id):
        bank_name = ""
        for line in partner_id.bank_ids:
            if line and line.x_branch_bank:
                bank_name = line.bank_id.name.strip() + " - " + line.x_branch_bank.strip()
                break
            elif line:
                bank_name = line.bank_id.name.strip()
                break
        return bank_name.strip()

    def get_bank_address_partner(self, partner_id):
        bank_add = ""
        for line in partner_id.bank_ids:
            if line.bank_id:
                bank_add = line.bank_id.street
                break
        return bank_add.strip()

    def get_account_number_company(self, company_id):
        acc_number = ""
        for item in company_id.partner_id.bank_ids:
            if item.acc_number:
                acc_number = item.acc_number
                break
        return acc_number.strip()

    @api.model
    def get_amount_text_vnd(self, amount):
        res = num2word(int(amount))
        if res.endswith("năm"):
            if int(str(int(amount))[-2:]) > 10:
                res = res[:-3] + "lăm"
        if res:
            res += ' đồng chẵn.'
        return res

    @api.model
    def get_amount_text_vnd_no_currency(self, amount):
        res = num2word(int(amount))
        if res.endswith("năm"):
            if int(str(int(amount))[-2:]) > 10:
                res = res[:-3] + "lăm"
        return res

    def action_print_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/to_loan_management/unc/%s' % (self.id),
            'target': 'current'
        }

    # def action_print_uy_nhiem_chi_refund(self, refund_payment_id, docs_templ):
    #     docs = docs_templ
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #
    #         # Ủy nhiệm chi BIDV
    #         if docs_templ.file_name == 'uy_nhiem_chi.docx':
    #             context['company_name'] = check(refund_payment_id.refund_id.company_id.name)
    #             # context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['branch_name'] = self.get_bank_name_partner(refund_payment_id.disbursement_id.partner_id)
    #             context['partner_name'] = check(refund_payment_id.disbursement_id.partner_id.name).strip()
    #             context['acc_partner_benficiary'] = self.get_account_number_partner(
    #                 refund_payment_id.disbursement_id.partner_id)
    #             context['partner_bank'] = self.get_bank_name_partner(refund_payment_id.disbursement_id.partner_id)
    #             context['amount'] = "{:,.0f}".format(refund_payment_id.matched_amount)
    #             context['amount_text'] = self.get_amount_text_vnd_no_currency(refund_payment_id.matched_amount)
    #             context['description'] = 'Hoàn gốc cho khế ước - ' + check(refund_payment_id.disbursement_id.indenture)
    #         #
    #         # # Ủy nhiệm chi VCB
    #         if docs_templ.file_name == 'uy_nhiem_chi_vcb.docx':
    #             context['company_name'] = check(refund_payment_id.refund_id.company_id.name)
    #             context['company_address'] = check(refund_payment_id.refund_id.company_id.street)
    #             # context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['branch_name'] = self.get_bank_name_partner(refund_payment_id.disbursement_id.partner_id)
    #             context['partner_name'] = check(refund_payment_id.disbursement_id.partner_id.name).strip()
    #             context['partner_address'] = check(refund_payment_id.disbursement_id.partner_id.street).strip()
    #             context['acc_partner_benficiary'] = self.get_account_number_partner(
    #                 refund_payment_id.disbursement_id.partner_id)
    #             context['partner_bank'] = self.get_bank_name_partner(refund_payment_id.disbursement_id.partner_id)
    #             context['amount'] = "{:,.0f}".format(refund_payment_id.matched_amount)
    #             context['amount_text'] = self.get_amount_text_vnd_no_currency(refund_payment_id.matched_amount)
    #             context['description'] = 'Hoàn gốc cho khế ước - ' + check(refund_payment_id.disbursement_id.indenture)
    #         #
    #         # # Ủy nhiệm chi VTB
    #         if docs_templ.file_name == 'uy_nhiem_chi_vtb.docx':
    #             context['company_name'] = check(refund_payment_id.refund_id.company_id.name)
    #             context['company_address'] = check(refund_payment_id.refund_id.company_id.street)
    #             # context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['branch_name'] =  self.get_bank_name_partner(refund_payment_id.disbursement_id.partner_id)
    #             context['partner_name'] = check(refund_payment_id.disbursement_id.partner_id.name).strip()
    #             context['acc_partner_benficiary'] = self.get_account_number_partner(
    #                 refund_payment_id.disbursement_id.partner_id)
    #             context['partner_bank'] = self.get_bank_name_partner(refund_payment_id.disbursement_id.partner_id)
    #             context['amount'] = "{:,.0f}".format(refund_payment_id.matched_amount)
    #             context['amount_text'] = self.get_amount_text_vnd_no_currency(refund_payment_id.matched_amount)
    #             context['description'] = 'Hoàn gốc cho khế ước - ' + check(refund_payment_id.disbursement_id.indenture)
    #
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

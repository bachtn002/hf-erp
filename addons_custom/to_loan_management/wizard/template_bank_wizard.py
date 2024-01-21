from odoo import models, fields, api, _
from io import BytesIO
from tempfile import NamedTemporaryFile
# from docxtpl import DocxTemplate, Listing, RichText
import codecs
from odoo.exceptions import ValidationError


def convert_date(date_cv):
    if date_cv:
        return date_cv.strftime('%d/%m/%Y')
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


class TemplateBankWizard(models.TransientModel):
    _name = 'template.bank.wizard'
    _description = 'Print'

    word_template_id = fields.Many2one('word.template', 'Word Template', required=True)
    borrow_disbursement_id = fields.Many2one('loan.borrow.disbursement', 'Disbursement')
    disbursement_payment_match_id = fields.Many2one('loan.borrow.disbursement.payment.match',
                                                    'Disbursement Payment Match')
    partner_id = fields.Many2one('res.partner', 'Partner')
    file_name = fields.Char(string='File name')
    disbursement_detail_id = fields.Many2one('loan.borrow.disbursement.dt',
                                             'Disbursement Detail')

    @api.onchange('word_template_id')
    def onchange_method_word_template(self):
        self.file_name = self.word_template_id.file_name
        if self.disbursement_detail_id:
            partner_ids_list = []
            if self.disbursement_detail_id:
                if self.disbursement_detail_id.partner_id.id not in partner_ids_list:
                    partner_ids_list.append(self.disbursement_detail_id.partner_id.id)
                if partner_ids_list:
                    return {'domain': {
                        'partner_id': [('id', 'in', partner_ids_list), '|', ('company_id', '=', False),
                                       ('company_id', '=', self.borrow_disbursement_id.company_id.id)]}}
            else:
                return {'domain': {
                    'partner_id': [('id', 'in', []), '|', ('company_id', '=', False),
                                   ('company_id', '=', self.borrow_disbursement_id.company_id.id)]}}

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

    @api.model
    def get_amount_to_word(self, amount):
        res = num2word(int(amount))
        if res.endswith("năm"):
            if int(str(int(amount))[-2:]) > 10:
                res = res[:-3] + "lăm"
        amount_int = int(amount)
        if amount > amount_int:
            if int(str(amount).split('.')[1]) <= 9 and len(str(amount).split('.')[1]) == 1:
                res2 = num2word(int(str(amount).split('.')[1] + "0")).lower()
                if res2.endswith("năm"):
                    if int(str(amount).split('.')[1]) == 5:
                        res2 = res2[:-3] + "lăm"
                if res2 != '':
                    result = res + ' đô la Mỹ và ' + res2 + ' xen.'
            elif int(str(amount).split('.')[1]) <= 9 and len(str(amount).split('.')[1]) == 2:
                res2 = num2word(int(str(amount).split('.')[1])).lower()
                if res2.endswith("năm"):
                    if int(str(amount).split('.')[1]) == 5:
                        res2 = res2[:-3] + "lăm"
                if res2 != '':
                    result = res + ' đô la Mỹ và ' + res2 + ' xen.'
            else:
                res2 = num2word(int(str(amount).split('.')[1])).lower()
                if res2 != '':
                    result = res + ' đô la Mỹ ' + res2 + ' xen.'
        else:
            result = res + ' đô la Mỹ.'
        return result

    def action_print_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/to_loan_management/wizard/%s' % (self.id),
            'target': 'current'
        }

    # def action_print_doc_2(self, disbursement_id, docs_templ, template_wizard, disbursement_dt_id):
    #     docs = docs_templ
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #
    #         # Mẫu phiếu BIDV
    #         if docs_templ.file_name == 'cam_ket_no_chung_tu.docx':
    #             context['branch_name'] = disbursement_id.partner_id.name if disbursement_id.partner_id else ""
    #             context['date'] = convert_date(disbursement_dt_id.create_date)
    #             context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #             if disbursement_dt_id.currency_id.name == "VND":
    #                 context['amount'] = "{:,.0f}".format(disbursement_dt_id.value)
    #             elif disbursement_dt_id.currency_id.name == "USD":
    #                 context['amount'] = "{:,.2f}".format(disbursement_dt_id.value)
    #             context['currency'] = check(disbursement_dt_id.currency_id.name)
    #             context['beneficiary'] = check(disbursement_dt_id.partner_id.name).strip()
    #
    #         if docs_templ.file_name == 'giay_giai_ngan_USD.docx':
    #             context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #             context['branch'] = disbursement_id.partner_id.name if disbursement_id.partner_id else ""
    #             context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #             context['loan_duration'] = check(disbursement_id.loan_duration)
    #             context['date_contract'] = convert_date(
    #                 disbursement_id.order_id.date_confirmed) if disbursement_id.order_id else ""
    #             table_list_data = []
    #             total_amount = 0
    #             contract_code = ""
    #             list_partner_id = []
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == 'USD':
    #                     if contract_code == "":
    #                         contract_code += check(line.origin)
    #                     else:
    #                         contract_code += ", " + check(line.origin)
    #                     partner_id = check(line.partner_id.id)
    #                     if partner_id not in list_partner_id and partner_id != "":
    #                         amount_line = 0
    #                         description_line = ""
    #                         for item in disbursement_id.disbursement_dt_ids:
    #                             if item.currency_id.name == 'USD':
    #                                 partner_id_2 = item.partner_id.id
    #                                 if partner_id == partner_id_2:
    #                                     amount_line += item.value
    #                                     if description_line == "":
    #                                         description_line += check(item.description)
    #                                     else:
    #                                         description_line += ", " + check(item.description)
    #
    #                         partner_name = check(line.partner_id.name).strip()
    #                         if partner_name != "":
    #                             infor = {}
    #                             infor['description'] = description_line
    #                             infor['amount'] = "{:,.2f}".format(amount_line)
    #                             total_amount += amount_line
    #                             # infor['partner_name'] = RichText()
    #                             infor['partner_name'].add(partner_name, size=17, font='Times New Roman')
    #                             infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                             if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                                 infor['bank_name'] = check(
    #                                     line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                                     line.beneficiary_bank_id.x_branch_bank).strip()
    #                             elif not line.beneficiary_bank_id.x_branch_bank:
    #                                 infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                             infor['swift'] = check(line.beneficiary_bank_id.x_swift_bank)
    #                             table_list_data.append(infor)
    #                     if partner_id not in list_partner_id:
    #                         list_partner_id.append(partner_id)
    #             context['list_data'] = table_list_data
    #             context['total_amount'] = "{:,.2f}".format(total_amount)
    #             context['contract_code'] = contract_code
    #             if total_amount > 0:
    #                 context['total_amount_text'] = self.get_amount_to_word(total_amount)
    #             else:
    #                 context['total_amount_text'] = ""
    #
    #         if docs_templ.file_name == 'giay_giai_ngan_VND.docx':
    #             context['branch'] = check(disbursement_id.partner_id.name).strip()
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #             context['loan_duration'] = check(disbursement_id.loan_duration)
    #             context['date_contract'] = convert_date(
    #                 disbursement_id.order_id.date_confirmed) if disbursement_id.order_id else ""
    #
    #             table_list_data = []
    #             total_amount = 0
    #             contract_code = ""
    #             list_partner_id = []
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "VND":
    #                     if contract_code == "":
    #                         contract_code += check(line.origin)
    #                     elif line.origin:
    #                         contract_code += ", " + check(line.origin)
    #                     partner_id = check(line.partner_id.id)
    #                     if partner_id not in list_partner_id and partner_id != "":
    #                         amount_line = 0
    #                         description_line = ""
    #                         for item in disbursement_id.disbursement_dt_ids:
    #                             partner_id_2 = item.partner_id.id
    #                             if partner_id == partner_id_2:
    #                                 amount_line += item.value
    #                                 if description_line == "":
    #                                     description_line += check(item.description)
    #                                 else:
    #                                     description_line += ", " + check(item.description)
    #
    #                         partner_name = check(line.partner_id.name).strip()
    #                         if partner_name != "":
    #                             infor = {}
    #                             infor['description'] = description_line
    #                             infor['amount'] = "{:,.0f}".format(amount_line)
    #                             total_amount += amount_line
    #                             infor['partner_name'] = partner_name
    #                             infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                             if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                                 infor['bank_name'] = check(
    #                                     line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                                     line.beneficiary_bank_id.x_branch_bank).strip()
    #                             elif not line.beneficiary_bank_id.x_branch_bank:
    #                                 infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                             table_list_data.append(infor)
    #                     if partner_id not in list_partner_id:
    #                         list_partner_id.append(partner_id)
    #             context['list_data'] = table_list_data
    #             context['total_amount'] = "{:,.0f}".format(total_amount)
    #             context['contract_code'] = contract_code
    #             if total_amount > 0:
    #                 context['total_amount_text'] = self.get_amount_text_vnd(total_amount)
    #             else:
    #                 context['total_amount_text'] = ""
    #
    #         if docs_templ.file_name == 'hd_mua_ban_ngoai_te.docx':
    #             context['branch'] = disbursement_id.partner_id.name if disbursement_id.partner_id else ""
    #             context['address_branch'] = disbursement_id.partner_id.street if disbursement_id.partner_id else ""
    #             context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #             context['company_address'] = disbursement_id.company_id.street if disbursement_id.company_id else ""
    #             total_amount = 0
    #             description_line = ""
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "USD":
    #                     total_amount += line.value
    #                     if description_line == "":
    #                         description_line += check(line.description)
    #                     else:
    #                         description_line += ", " + check(line.description)
    #             context['amount'] = "{:,.2f}".format(total_amount)
    #             context[
    #                 'description'] = description_line
    #
    #         if docs_templ.file_name == 'lenh_chuyen_tien.docx':
    #             total_amount = 0
    #             description = ""
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.partner_id.id == disbursement_dt_id.partner_id.id:
    #                     total_amount += line.value
    #                     if description == "":
    #                         description += check(line.description)
    #                     else:
    #                         description += ", " + check(line.description)
    #
    #             context['currency'] = check(disbursement_dt_id.currency_id.name)
    #
    #             if disbursement_dt_id.currency_id.name == 'VND':
    #                 context['amount_text'] = self.get_amount_text_vnd(total_amount)
    #                 context['amount'] = "{:,.0f}".format(total_amount)
    #             else:
    #                 context['amount_text'] = self.get_amount_to_word(total_amount)
    #                 context['amount'] = "{:,.2f}".format(total_amount)
    #
    #             context['company_address'] = disbursement_id.company_id.street if disbursement_id.company_id else ""
    #             context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #             context['acc_company'] = self.get_account_number_company(
    #                 disbursement_id.company_id) if disbursement_id.company_id else ""
    #             beneficiary_bank = ''
    #             if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #                 beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     beneficiary_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             else:
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             context['beneficiary_bank'] = check(beneficiary_bank)
    #             context['bene_bank_add'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #             # context['beneficiary'] = RichText()
    #             context['beneficiary'].add(disbursement_dt_id.partner_id.name.strip(), size=17, font='Times New Roman', italic=True, bold=True)
    #             context['acc_number'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #             context['beneficiary_add'] = check(disbursement_dt_id.partner_id.street)
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #             context[
    #                 'description'] = description
    #             context[
    #                 'swift'] = check(disbursement_dt_id.beneficiary_bank_id.x_swift_bank)
    #
    #         # VietComBank
    #         if docs_templ.file_name == 'giay_de_nghi_mua_ngoai_te_vcb.docx':
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             contract_code = ""
    #             total_amount = 0
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "USD":
    #                     total_amount += line.value
    #                     if contract_code == "":
    #                         contract_code += check(line.origin)
    #                     elif line.origin:
    #                         contract_code += ", " + check(line.origin)
    #             context['amount_usd'] = "{:,.2f}".format(total_amount)
    #             context['amount_text'] = self.get_amount_to_word(total_amount)
    #             context['contract_code'] = contract_code
    #
    #         if docs_templ.file_name == 'lenh_chuyen_tien_vcb.docx':
    #
    #             total_amount = 0
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.partner_id.id == disbursement_dt_id.partner_id.id:
    #                     total_amount += line.value
    #             context['currency'] = check(disbursement_dt_id.currency_id.name)
    #             if context['currency'] == 'VND':
    #                 context['amount'] = "{:,.0f}".format(total_amount)
    #                 context['amount_text'] = self.get_amount_text_vnd(total_amount)
    #             else:
    #                 context['amount'] = "{:,.2f}".format(total_amount)
    #                 context['amount_text'] = self.get_amount_to_word(total_amount)
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             bank_partner = ''
    #             if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #                 bank_partner += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     bank_partner += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             else:
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     bank_partner += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             context['bank_partner'] = check(bank_partner)
    #             context['bank_partner_add'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #             context['beneficiary'] = disbursement_dt_id.partner_id.name if disbursement_dt_id.partner_id else ""
    #             context['beneficiary_address'] = check(disbursement_dt_id.partner_id.street)
    #             context['acc_bank_partner'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #             context['bank_partner_code'] = check(disbursement_dt_id.beneficiary_bank_id.x_swift_bank)
    #
    #         # VietComBank NEW
    #         if docs_templ.file_name == 'cam_ket_tra_chung_tu_vcb.docx':
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['vendor'] = check(disbursement_dt_id.partner_id.name).strip()
    #             context['curency_name'] = check(disbursement_dt_id.currency_id.name)
    #             if disbursement_dt_id.currency_id.name == 'VND':
    #                 context['amount'] = "{:,.0f}".format(disbursement_dt_id.value)
    #                 context['amount_text'] = self.get_amount_text_vnd(disbursement_dt_id.value)
    #             else:
    #                 context['amount'] = "{:,.2f}".format(disbursement_dt_id.value)
    #                 context['amount_text'] = self.get_amount_to_word(disbursement_dt_id.value)
    #             context['contract_code'] = check(disbursement_dt_id.origin)
    #             for line in disbursement_dt_id.purchase_order_ids:
    #                 if line.date_approve:
    #                     context['sign_day'] = convert_date(line.date_approve)
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         if docs_templ.file_name == 'giay_nhan_no_vcb.docx':
    #             context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #             context['date_accept'] = convert_date(
    #                 disbursement_id.order_id.date_confirmed) if disbursement_id.order_id.date_confirmed else ""
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['duration'] = check(disbursement_id.loan_duration)
    #             context['amount_contract'] = "{:,.0f}".format(
    #                 disbursement_id.order_id.loan_amount) if disbursement_id.order_id.loan_amount else ""
    #             context['currency'] = check(disbursement_id.order_id.currency_id.name)
    #             context['authorized_person'] = check(disbursement_id.authorized_person).strip()
    #             context['authorization_letter'] = check(disbursement_id.authorization_letter).strip()
    #             context['authorized_date'] = convert_date(disbursement_id.authorized_date)
    #
    #             total_amount = 0
    #             currency_line = ""
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if currency_line == "":
    #                     currency_line = line.currency_id.name
    #                 if currency_line == "VND":
    #                     context['total_amount'] = "{:,.0f}".format(
    #                         disbursement_id.amount) if disbursement_id.amount else ""
    #                     context['total_am_text'] = self.get_amount_text_vnd(
    #                         disbursement_id.amount) if disbursement_id.amount else ""
    #                     break
    #                 elif currency_line == "USD" and line.currency_id.name == "USD":
    #                     total_amount += line.value
    #
    #             context['amount_text'] = self.get_amount_text_vnd(
    #                 disbursement_id.order_id.loan_amount) if disbursement_id.order_id else ""
    #
    #             context['total_currency'] = check(currency_line)
    #             if currency_line == 'USD':
    #                 context['total_amount'] = "{:,.2f}".format(total_amount)
    #                 context['total_am_text'] = self.get_amount_to_word(total_amount)
    #             description = ""
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if description == "":
    #                     description += check(line.description)
    #                 elif line.description:
    #                     description += ", " + check(line.description)
    #
    #             context['description'] = description
    #             context['amount'] = "{:,.2f}".format(disbursement_id.amount)
    #             context['amount_text_2'] = self.get_amount_text_vnd(
    #                 disbursement_id.amount) if disbursement_id.amount else ""
    #             context['description'] = description
    #             context['rate_type'] = check(disbursement_id.order_id.interest_rate_type_id.flat_rate)
    #             context['rate_period'] = ''
    #             if check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'week':
    #                 context['rate_period'] = 'tuần'
    #             elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'month':
    #                 context['rate_period'] = 'tháng'
    #             elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'year':
    #                 context['rate_period'] = 'năm'
    #             else:
    #                 context['rate_period'] = ''
    #             if disbursement_id.order_id.expiry_interest_rate_type_id:
    #                 name = disbursement_id.order_id.expiry_interest_rate_type_id.name if disbursement_id.order_id.expiry_interest_rate_type_id.name else ""
    #                 # if disbursement_id.order_id.expiry_interest_rate_type_id.type == 'flat':
    #                 #     type = "Lãi suất Cố định"
    #                 # elif disbursement_id.order_id.expiry_interest_rate_type_id.type == 'floating':
    #                 #     type = "Lãi suất Thả nổi"
    #                 # else:
    #                 #     type = ""
    #                 context['expiry_interest_rate_type'] = check(name)
    #
    #         # HD mua, ban ngoai te VietComBank NEW
    #         if docs_templ.file_name == 'hop_dong_mua_ban_ngoai_te_vcb.docx':
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['branch_name_upper'] = check(disbursement_id.partner_id.name).strip().upper()
    #             context['branch_address'] = check(disbursement_id.partner_id.street).strip()
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             total_amount = 0
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "USD":
    #                     total_amount += line.value
    #             context['amount'] = "{:,.2f}".format(total_amount)
    #
    #         # ViettinBank
    #         if docs_templ.file_name == 'de_nghi_mua_ngoai_te_vtb.docx':
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             context['bank_acc'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #             description_line = ""
    #             total_amount = 0
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "USD":
    #                     total_amount += line.value
    #                     if description_line == "":
    #                         description_line += check(line.description)
    #                     elif line.description:
    #                         description_line += ", " + check(line.description)
    #
    #             context['description'] = check(description_line)
    #             context['amount'] = "{:,.2f}".format(total_amount)
    #             context['amount_text'] = self.get_amount_to_word(total_amount)
    #
    #         if docs_templ.file_name == 'lenh_chuyen_tien_vtb.docx':
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #
    #             total_amount = 0
    #             description = ""
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.partner_id.id == disbursement_dt_id.partner_id.id:
    #                     total_amount += line.value
    #                     if description == "":
    #                         description += check(line.description)
    #                     elif line.description:
    #                         description += ", " + line.description
    #
    #             context['currency'] = check(disbursement_dt_id.currency_id.name)
    #             if context['currency'] == 'VND':
    #                 context['amount'] = "{:,.0f}".format(total_amount)
    #                 context['amount_text'] = self.get_amount_text_vnd(total_amount)
    #             else:
    #                 context['amount'] = "{:,.2f}".format(total_amount)
    #                 context['amount_text'] = self.get_amount_to_word(total_amount)
    #
    #             context['description'] = check(description)
    #             beneficiary_bank = ''
    #             if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #                 beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     beneficiary_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             else:
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             context['beneficiary_bank'] = check(beneficiary_bank)
    #             context['bene_bank_add'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #             context['beneficiary'] = check(disbursement_dt_id.partner_id.name).strip()
    #             context['acc_number'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #             context['beneficiary_add'] = check(disbursement_dt_id.partner_id.street)
    #             context['bank_code'] = check(disbursement_dt_id.beneficiary_bank_id.x_swift_bank)
    #
    #         if docs_templ.file_name == 'giay_nhan_no_vtb_usd.docx':
    #             context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #             context['date_contract'] = convert_date(
    #                 disbursement_id.order_id.date_confirmed) if disbursement_id.order_id.date_confirmed else ""
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['branch_upper'] = check(disbursement_id.partner_id.name.upper())
    #             context['amount_contract'] = "{:,.0f}".format(
    #                 disbursement_id.order_id.loan_amount) if disbursement_id.order_id else ""
    #             context['bank_acc_partner'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['authorized_date'] = convert_date(
    #                 disbursement_id.authorized_date) if disbursement_id.authorized_date else "........................................"
    #             context['authorized_person'] = disbursement_id.authorized_person.strip() if disbursement_id.authorized_person else "........................................"
    #             context['authorization_letter'] = check(disbursement_id.authorization_letter).strip()
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #             total_no = 0
    #             total_amount = 0
    #             contract_code = ""
    #             description_line = ""
    #             table_list_data = []
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "USD" and line.x_type == "invoice":
    #                     infor = {}
    #                     # Tong tien o cac don hang
    #                     total_invoice = 0
    #                     contract_code = ""
    #                     for item in line.invoice_ids:
    #                         if item.currency_id.name == 'USD':
    #                             total_invoice += item.amount_total
    #                         if contract_code == "":
    #                             contract_code += check(item.x_number_invoice)
    #                         else:
    #                             contract_code += ", " + check(item.x_number_invoice)
    #                     # Mo ta cua cac line
    #                     if description_line == "":
    #                         description_line += check(line.description)
    #                     elif line.description:
    #                         description_line += ", " + check(line.description)
    #                     # Tong tien cac lan thanh toan
    #                     total_no += line.value
    #                     infor['amount'] = "{:,.2f}".format(total_invoice)
    #                     infor['amount_no'] = "{:,.2f}".format(line.value)
    #                     total_amount += total_invoice
    #                     infor['partner_name'] = line.partner_id.name
    #                     infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                     if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                         infor['bank_name'] = check(
    #                             line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                             line.beneficiary_bank_id.x_branch_bank).strip()
    #                     elif not line.beneficiary_bank_id.x_branch_bank:
    #                         infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                     # infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip() + ", " + check(
    #                     #     line.beneficiary_bank_id.x_branch_bank).strip()
    #                     infor['contract_code'] = check(contract_code)
    #                     infor['contract_date'] = convert_date(line.create_date)
    #                     table_list_data.append(infor)
    #
    #                 elif line.currency_id.name == "USD":
    #                     infor = {}
    #                     # Tong tien o cac don hang
    #                     total_purchase = 0
    #                     for item in line.purchase_order_ids:
    #                         if item.currency_id.name == 'USD':
    #                             total_purchase += item.amount_total
    #
    #                     # Mo ta cua cac line
    #                     if description_line == "":
    #                         description_line += check(line.description)
    #                     elif line.description:
    #                         description_line += ", " + check(line.description)
    #
    #                     # Tong tien cac lan thanh toan
    #                     total_no += line.value
    #                     infor['amount'] = "{:,.2f}".format(total_purchase)
    #                     infor['amount_no'] = "{:,.2f}".format(line.value)
    #                     total_amount += total_purchase
    #                     infor['partner_name'] = line.partner_id.name
    #                     infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                     if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                         infor['bank_name'] = check(
    #                             line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                             line.beneficiary_bank_id.x_branch_bank).strip()
    #                     elif not line.beneficiary_bank_id.x_branch_bank:
    #                         infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                     # infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip() + ", " + check(
    #                     #     line.beneficiary_bank_id.x_branch_bank).strip()
    #                     infor['contract_code'] = check(line.origin)
    #                     infor['contract_date'] = convert_date(line.create_date)
    #                     if contract_code == "":
    #                         contract_code += check(line.origin)
    #                     elif line.origin:
    #                         contract_code += ", " + check(line.origin)
    #                     table_list_data.append(infor)
    #
    #             context['description'] = description_line
    #             context['list_data'] = table_list_data
    #             context['total_amount'] = "{:,.2f}".format(total_amount)
    #             context['total_no'] = "{:,.2f}".format(total_no)
    #             context['rate_type'] = check(disbursement_id.order_id.interest_rate_type_id.flat_rate)
    #             context['rate_period'] = ''
    #             if check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'week':
    #                 context['rate_period'] = 'Mỗi tuần'
    #             elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'month':
    #                 context['rate_period'] = 'Mỗi tháng'
    #             elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'year':
    #                 context['rate_period'] = 'Mỗi năm'
    #             else:
    #                 context['rate_period'] = ''
    #             if disbursement_id.order_id.expiry_interest_rate_type_id:
    #                 name = disbursement_id.order_id.expiry_interest_rate_type_id.name if disbursement_id.order_id.expiry_interest_rate_type_id.name else ""
    #                 context['expiry_interest_rate_type'] = check(name)
    #
    #         if docs_templ.file_name == 'giay_nhan_no_vtb_vnd.docx':
    #             context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #             context['date_contract'] = convert_date(
    #                 disbursement_id.order_id.date_confirmed) if disbursement_id.order_id.date_confirmed else ""
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #             context['branch_upper'] = check(disbursement_id.partner_id.name.upper())
    #             context['amount_contract'] = "{:,.0f}".format(
    #                 disbursement_id.order_id.loan_amount) if disbursement_id.order_id else ""
    #             context['bank_acc_partner'] = self.get_bank_name_partner(disbursement_id.partner_id)
    #             context['authorized_date'] = convert_date(disbursement_id.authorized_date) if disbursement_id.authorized_date else "........................................"
    #             context['authorized_person'] = disbursement_id.authorized_person.strip() if disbursement_id.authorized_person else "................................................"
    #             context['authorization_letter'] = check(disbursement_id.authorization_letter).strip()
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #             total_no = 0
    #             total_amount = 0
    #             contract_code = ""
    #             description_line = ""
    #             table_list_data = []
    #             for line in disbursement_id.disbursement_dt_ids:
    #                 if line.currency_id.name == "VND" and line.x_type == "invoice":
    #                     infor = {}
    #                     # Tong tien o cac don hang
    #                     contract_code = ""
    #                     total_invoice = 0
    #                     for item in line.invoice_ids:
    #                         if item.currency_id.name == 'VND':
    #                             total_invoice += item.amount_total
    #                         if contract_code == "":
    #                             contract_code += check(item.x_number_invoice)
    #                         else:
    #                             contract_code += ", " + check(item.x_number_invoice)
    #                     # Mo ta cua cac line
    #                     if description_line == "":
    #                         description_line += check(line.description)
    #                     elif line.description:
    #                         description_line += ", " + check(line.description)
    #                     # Tong tien cac lan thanh toan
    #                     total_no += line.value
    #                     infor['amount'] = "{:,.0f}".format(total_invoice)
    #                     infor['amount_no'] = "{:,.0f}".format(line.value)
    #                     total_amount += total_invoice
    #                     infor['partner_name'] = line.partner_id.name
    #                     infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                     if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                         infor['bank_name'] = check(
    #                             line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                             line.beneficiary_bank_id.x_branch_bank).strip()
    #                     elif not line.beneficiary_bank_id.x_branch_bank:
    #                         infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                     infor['contract_code'] = check(contract_code)
    #                     infor['contract_date'] = convert_date(line.create_date)
    #                     table_list_data.append(infor)
    #                 elif line.currency_id.name == "VND":
    #                     infor = {}
    #                     # Tong tien o cac don hang
    #                     total_purchase = 0
    #                     for item in line.purchase_order_ids:
    #                         if item.currency_id.name == 'VND':
    #                             total_purchase += item.amount_total
    #
    #                     # Mo ta cua cac line
    #                     if description_line == "":
    #                         description_line += check(line.description)
    #                     elif line.description:
    #                         description_line += ", " + check(line.description)
    #
    #                     # Tong tien cac lan thanh toan
    #                     total_no += line.value
    #                     infor['amount'] = "{:,.0f}".format(total_purchase)
    #                     infor['amount_no'] = "{:,.0f}".format(line.value)
    #                     total_amount += total_purchase
    #                     infor['partner_name'] = line.partner_id.name
    #                     infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                     if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                         infor['bank_name'] = check(
    #                             line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                             line.beneficiary_bank_id.x_branch_bank).strip()
    #                     elif not line.beneficiary_bank_id.x_branch_bank:
    #                         infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                     # infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip() + ", " + check(
    #                     #     line.beneficiary_bank_id.x_branch_bank).strip()
    #                     infor['contract_code'] = check(line.origin)
    #                     infor['contract_date'] = convert_date(line.create_date)
    #                     if contract_code == "":
    #                         contract_code += check(line.origin)
    #                     elif line.origin:
    #                         contract_code += ", " + check(line.origin)
    #                     table_list_data.append(infor)
    #
    #             context['description'] = description_line
    #             context['list_data'] = table_list_data
    #             context['total_amount'] = "{:,.0f}".format(total_amount)
    #             context['total_no'] = "{:,.0f}".format(total_no)
    #             context['amount_text'] = self.get_amount_text_vnd(total_no)
    #             context['rate_type'] = check(disbursement_id.order_id.interest_rate_type_id.flat_rate)
    #             context['rate_period'] = ''
    #             if check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'week':
    #                 context['rate_period'] = 'Mỗi tuần'
    #             elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'month':
    #                 context['rate_period'] = 'Mỗi tháng'
    #             elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'year':
    #                 context['rate_period'] = 'Mỗi năm'
    #             else:
    #                 context['rate_period'] = ''
    #
    #             if disbursement_id.order_id.expiry_interest_rate_type_id:
    #                 name = disbursement_id.order_id.expiry_interest_rate_type_id.name if disbursement_id.order_id.expiry_interest_rate_type_id.name else ""
    #                 context['expiry_interest_rate_type'] = check(name)
    #         # Giấy nộp thuế
    #         if docs_templ.file_name == 'giay_nop_thue.docx':
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             context['mst'] = check(disbursement_id.company_id.partner_id.vat)
    #             context['branch'] = check(disbursement_id.partner_id.name).strip()
    #             context['kbnn'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.name)
    #             context['add_kbnn'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #             context['name_partner'] = check(disbursement_dt_id.partner_id.name).strip()
    #             declaration_number = ""
    #             date = ""
    #             table_list_data = []
    #             total_amount = 0
    #             for line in disbursement_dt_id.lc_ids:
    #                 if declaration_number == "":
    #                     declaration_number = line.customs_declaration_number
    #                 if date == "":
    #                     date = convert_date(line.date)
    #                 for item in line.cost_lines:
    #                     infor = {}
    #                     infor['content'] = check(item.account_id.name)
    #                     infor['amount'] = "{:,.0f}".format(item.price_unit)
    #                     total_amount += item.price_unit
    #                     table_list_data.append(infor)
    #             context['declaration_number'] = check(declaration_number)
    #             context['date'] = date
    #             context['list_data'] = table_list_data
    #             context['total_amount'] = "{:,.0f}".format(total_amount)
    #             res = num2word(int(total_amount))
    #             context['text_total_amount'] = res + ' đồng.'
    #
    #         # Ủy nhiệm chi BIDV
    #         if docs_templ.file_name == 'uy_nhiem_chi.docx':
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['branch_name'] = check(disbursement_id.payment_account_id.bank_id.name)
    #             context['partner_name'] = check(disbursement_dt_id.partner_id.name).strip()
    #             context['acc_partner_benficiary'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #             partner_bank = ''
    #             if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #                 partner_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     partner_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             else:
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     partner_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             context['partner_bank'] = check(partner_bank)
    #             context['amount'] = "{:,.0f}".format(disbursement_dt_id.value_natural_currency)
    #             context['amount_text'] = self.get_amount_text_vnd_no_currency(disbursement_dt_id.value_natural_currency)
    #             context['description'] = check(disbursement_dt_id.description)
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #             context['branch_payment'] = check(disbursement_id.payment_account_id.x_branch_bank)
    #
    #         # Ủy nhiệm chi VCB
    #         if docs_templ.file_name == 'uy_nhiem_chi_vcb.docx':
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['branch_name'] = check(disbursement_id.payment_account_id.bank_id.name)
    #             if disbursement_id.payment_account_id.x_branch_bank:
    #                 context['branch_name'] += ' - ' + disbursement_id.payment_account_id.x_branch_bank
    #             context['partner_name'] = check(disbursement_dt_id.partner_id.name).strip()
    #             context['partner_address'] = check(disbursement_dt_id.partner_id.street)
    #             context['acc_partner_benficiary'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #             partner_bank = ''
    #             if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #                 partner_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     partner_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             else:
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     partner_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             context['partner_bank'] = check(partner_bank)
    #             context['amount'] = "{:,.0f}".format(disbursement_dt_id.value_natural_currency)
    #             context['amount_text'] = self.get_amount_text_vnd_no_currency(disbursement_dt_id.value_natural_currency)
    #             context['description'] = check(disbursement_dt_id.description)
    #             context['branch_payment'] = check(disbursement_id.payment_account_id.x_branch_bank)
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #
    #         # Ủy nhiệm chi VTB
    #         if docs_templ.file_name == 'uy_nhiem_chi_vtb.docx':
    #             context['company_name'] = check(disbursement_id.company_id.name)
    #             context['company_address'] = check(disbursement_id.company_id.street)
    #             context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #             context['branch_name'] = check(disbursement_id.payment_account_id.bank_id.name)
    #             if disbursement_id.payment_account_id.x_branch_bank:
    #                 context['branch_name'] += ' - ' + disbursement_id.payment_account_id.x_branch_bank
    #             context['partner_name'] = check(disbursement_dt_id.partner_id.name).strip()
    #             context['acc_partner_benficiary'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #             partner_bank = ''
    #             if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #                 partner_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     partner_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             else:
    #                 if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                     partner_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #             context['partner_bank'] = check(partner_bank)
    #             context['amount'] = "{:,.0f}".format(disbursement_dt_id.value_natural_currency)
    #             context['amount_text'] = self.get_amount_text_vnd_no_currency(disbursement_dt_id.value_natural_currency)
    #             context['description'] = check(disbursement_dt_id.description)
    #             context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

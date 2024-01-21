import codecs
from io import BytesIO

# from docxtpl import DocxTemplate, RichText

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from tempfile import NamedTemporaryFile
import ast

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

class LoanBorrowDisbursement(models.Model):
    _name = 'loan.borrow.disbursement'
    _description = 'Disbursement Plan Line'
    _inherit = 'abstract.loan.disbursement'

    order_id = fields.Many2one('loan.borrowing.order', string='Contract', required=True,
                               readonly=True, states={'draft': [('readonly', False)]},
                               help="The Borrowing Loan contract that the disbursement follows")
    partner_id = fields.Many2one(related='order_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', store=True, readonly=True)
    journal_id = fields.Many2one(related='order_id.journal_id', readonly=True)
    account_id = fields.Many2one(related='order_id.account_id', readonly=True)

    refund_line_ids = fields.One2many('loan.borrow.refund.line', 'disbursement_id',
                                  string='Refunds',
                                  help="The principal refund that schedules refund for this disbursement")
    interest_line_ids = fields.One2many('loan.borrow.interest.line', 'disbursement_id', string='Interests',
                                        help="The scheduled interests concerning to this disbursement")

    payment_match_ids = fields.One2many('loan.borrow.disbursement.payment.match', 'disbursement_id', string='Payment Matches', readonly=True)
    payment_ids = fields.Many2many('loan.disbursement.payment', 'disbursement_payment_borrow_disbursement_rel', 'disbursement_id', 'payment_id',
                                   string='Payments', compute='_compute_payment_ids', store=True)
    move_ids = fields.Many2many('account.move', 'acc_move_borrow_disbursement_rel', 'disbursement_id', 'move_id',
                                string="Journal Entries", compute='_compute_move_ids', store=True)
    purchase_order_ids = fields.Many2many('purchase.order', string='Contracts', compute='_compute_payment_ids', store=True)
    invoice_ids = fields.Many2many('account.move','loan_account_move_invoice_rel','loan_id','invoice_id', string='Invoices', compute='_compute_payment_ids', store=True)
    indenture = fields.Char(string="Indenture")

    disbursement_dt_ids = fields.One2many('loan.borrow.disbursement.dt','loan_disbursement_id',string='Detail')
    is_compute_by_dt = fields.Boolean(string='Compute By Disbursement Detail', default=True)
    authorization_letter = fields.Char(string="Authorization letter", tracking=True)
    authorized_person = fields.Char(string="Authorized person", tracking=True)
    authorized_date = fields.Date(string="Authorized date", tracking=True)
    partner_domain = fields.Many2one('res.partner', related='company_id.partner_id')
    payment_account_id = fields.Many2one('res.partner.bank', string='Payment account')
    # loan_duration = fields.Integer(string='Loan Duration', default=12, required=True,
    #                                readonly=True, states={'draft': [('readonly', False)]},
    #                                help="The duration (in months) of the loan contract.")
    # date_end = fields.Date(string='Contract End', tracking=True, compute='_compute_date_end', store=True, readonly=True, states={'draft': [('readonly', False)]},
    #                        help="The date on which this contract will become expired")
    #
    #
    # @api.depends('date_start', 'loan_duration')
    # def _compute_date_end(self):
    #     for r in self:
    #         if r.date_start and r.loan_duration:
    #             r.date_end = r.date_start + relativedelta(months=+r.loan_duration)

    @api.onchange('is_compute_by_dt','disbursement_dt_ids')
    def _onchange_disbursement_amount(self):
        if self.is_compute_by_dt and len(self.disbursement_dt_ids) > 0:
            self.amount = sum(x.value_natural_currency for x in self.disbursement_dt_ids)


    @api.depends('payment_match_ids.payment_id')
    def _compute_payment_ids(self):
        for r in self:
            r.payment_ids = r.payment_match_ids.mapped('payment_id')
            r.purchase_order_ids = r.payment_ids.mapped('purchase_order_ids')
            r.invoice_ids = r.payment_ids.mapped('invoice_ids')

    @api.depends('payment_ids.move_id')
    def _compute_move_ids(self):
        for r in self:
            r.move_ids = r.payment_ids.mapped('move_id')

    def _get_sequence(self):
        return self.env['ir.sequence'].next_by_code('loan.borrowing.disbursement') or '/'

    def _get_refund_line_model(self):
        return 'loan.borrow.refund.line'

    def _get_loan_interest_line_model(self):
        return 'loan.borrow.interest.line'

    def _get_payment_match_model(self):
        return 'loan.borrow.disbursement.payment.match'

    def _get_disbursement_payment_action_xml_id(self):
        return 'to_loan_management.action_loan_borrow_disbursement_payment_wizard'

    def action_confirm(self):
        result = super(LoanBorrowDisbursement, self).action_confirm()
        for item in self:
            if item.name == '/':
                item.name = self._get_sequence() or '/'
        return result

    def action_show_popup_choose_partner(self):
        self.ensure_one()
        return {
            'name': _('Print UNC'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'loan.borrowing.order.unc',
            'no_destroy': False,
            'target': 'new',
            'view_id': self.env.ref(
                'to_loan_management.loan_borrow_order_print_unc_wizard_form') and self.env.ref(
                'to_loan_management.loan_borrow_order_print_unc_wizard_form').id or False,
            'context': {'default_disbursement_id': self.id},
        }

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
                bank_name = line.bank_id.name.strip() + ", " + line.x_branch_bank.strip()
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

    def action_print_template_bidv(self):
        if self.disbursement_dt_ids:
            return {
                'type': 'ir.actions.act_url',
                'url': '/to_loan_management/bidv/%s' % (self.id),
                'target': 'current'
            }
        else:
            raise ValidationError(_('Hiện tại Không có khoản thanh toán nào'))

    def action_print_template_vcb(self):
        if self.disbursement_dt_ids:
            return {
                'type': 'ir.actions.act_url',
                'url': '/to_loan_management/vcb/%s' % (self.id),
                'target': 'current'
            }
        else:
            raise ValidationError(_('Hiện tại Không có khoản thanh toán nào'))

    def action_print_template_vtb(self):
        if self.disbursement_dt_ids:
            return {
                'type': 'ir.actions.act_url',
                'url': '/to_loan_management/vtb/%s' % (self.id),
                'target': 'current'
            }
        else:
            raise ValidationError(_('Hiện tại Không có khoản thanh toán nào'))

    # Cam kết nợ chứng từ BIDV
    # def cam_ket_no_chung_tu_bidv(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "cam_ket_no_chung_tu.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch_name'] = disbursement_id.partner_id.name if disbursement_id.partner_id else ""
    #         context['date'] = convert_date(disbursement_dt_id.create_date)
    #         context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #         if disbursement_dt_id.currency_id.name == "VND":
    #             context['amount'] = "{:,.0f}".format(disbursement_dt_id.value)
    #         elif disbursement_dt_id.currency_id.name == "USD":
    #             context['amount'] = "{:,.2f}".format(disbursement_dt_id.value)
    #         context['currency'] = check(disbursement_dt_id.currency_id.name)
    #         context['beneficiary'] = check(disbursement_dt_id.partner_id.name).strip()
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy giải ngân USD BIDV
    # def giay_giai_ngan_usd_bidv(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'giay_giai_ngan_USD.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #         context['branch'] = disbursement_id.partner_id.name if disbursement_id.partner_id else ""
    #         context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #         context['loan_duration'] = check(disbursement_id.loan_duration)
    #         context['date_contract'] = convert_date(
    #             disbursement_id.order_id.date_confirmed) if disbursement_id.order_id else ""
    #
    #         table_list_data = []
    #         total_amount = 0
    #         contract_code = ""
    #         list_partner_id = []
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == 'USD':
    #                 partner_id = check(line.partner_id.id)
    #                 if partner_id not in list_partner_id and partner_id != "":
    #                     amount_line = 0
    #                     description_line = ""
    #                     for item in disbursement_id.disbursement_dt_ids:
    #                         if item.currency_id.name == 'USD':
    #                             partner_id_2 = item.partner_id.id
    #                             if partner_id == partner_id_2:
    #                                 amount_line += item.value
    #                                 if description_line == "":
    #                                     description_line += check(item.description)
    #                                 else:
    #                                     description_line += ", " + check(item.description)
    #
    #                     partner_name = check(line.partner_id.name).strip()
    #                     if partner_name != "":
    #                         infor = {}
    #                         infor['description'] = description_line
    #                         infor['amount'] = "{:,.2f}".format(amount_line)
    #                         total_amount += amount_line
    #                         # infor['partner_name'] = RichText()
    #                         infor['partner_name'].add(partner_name, size=17, font='Times New Roman')
    #                         infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                         bank_name = ''
    #                         if line.beneficiary_bank_id.bank_id.name:
    #                             bank_name += check(line.beneficiary_bank_id.bank_id.name).strip()
    #                             if line.beneficiary_bank_id.x_branch_bank:
    #                                 bank_name += " - " + check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                         else:
    #                             if line.beneficiary_bank_id.x_branch_bank:
    #                                 bank_name += check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                         infor['bank_name'] = check(bank_name)
    #                         infor['swift'] = check(line.beneficiary_bank_id.x_swift_bank)
    #                         if contract_code == "":
    #                             contract_code += check(line.origin)
    #                         else:
    #                             contract_code += ", " + check(line.origin)
    #                         table_list_data.append(infor)
    #
    #                 if partner_id not in list_partner_id:
    #                     list_partner_id.append(partner_id)
    #         context['list_data'] = table_list_data
    #         context['total_amount'] = "{:,.2f}".format(total_amount)
    #         context['contract_code'] = contract_code.strip()
    #         if total_amount > 0:
    #             context['total_amount_text'] = self.get_amount_to_word(total_amount)
    #         else:
    #             context['total_amount_text'] = ""
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy giải ngân VND BIDV
    # def giay_giai_ngan_vnd_bidv(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'giay_giai_ngan_VND.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch'] = check(disbursement_id.partner_id.name).strip()
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #         context['loan_duration'] = check(disbursement_id.loan_duration)
    #         context['date_contract'] = convert_date(
    #             disbursement_id.order_id.date_confirmed) if disbursement_id.order_id else ""
    #
    #         table_list_data = []
    #         total_amount = 0
    #         contract_code = ""
    #         list_partner_id = []
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "VND":
    #                 partner_id = check(line.partner_id.id)
    #                 if partner_id not in list_partner_id and partner_id != "":
    #                     amount_line = 0
    #                     description_line = ""
    #                     for item in disbursement_id.disbursement_dt_ids:
    #                         partner_id_2 = item.partner_id.id
    #                         if partner_id == partner_id_2:
    #                             amount_line += item.value
    #                             if description_line == "":
    #                                 description_line += check(item.description)
    #                             else:
    #                                 description_line += ", " + check(item.description)
    #
    #                     partner_name = check(line.partner_id.name).strip()
    #                     if partner_name != "":
    #                         infor = {}
    #                         infor['description'] = description_line
    #                         infor['amount'] = "{:,.0f}".format(amount_line)
    #                         total_amount += amount_line
    #                         infor['partner_name'] = partner_name
    #                         infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                         bank_name = ''
    #                         if line.beneficiary_bank_id.bank_id.name:
    #                             bank_name += check(line.beneficiary_bank_id.bank_id.name).strip()
    #                             if line.beneficiary_bank_id.x_branch_bank:
    #                                 bank_name += " - " + check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                         else:
    #                             if line.beneficiary_bank_id.x_branch_bank:
    #                                 bank_name += check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                         infor['bank_name'] = check(bank_name)
    #                         if contract_code == "":
    #                             contract_code += check(line.origin)
    #                         elif line.origin:
    #                             contract_code += ", " + check(line.origin)
    #                         table_list_data.append(infor)
    #
    #                 if partner_id not in list_partner_id:
    #                     list_partner_id.append(partner_id)
    #         context['list_data'] = table_list_data
    #         context['total_amount'] = "{:,.0f}".format(total_amount)
    #         context['contract_code'] = contract_code
    #         if total_amount > 0:
    #             context['total_amount_text'] = self.get_amount_text_vnd(total_amount)
    #         else:
    #             context['total_amount_text'] = ""
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Hợp đồng mua bán ngoại tệ BIDV
    # def hop_dong_mua_ban_ngoai_te_bidv(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'hd_mua_ban_ngoai_te.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch'] = disbursement_id.partner_id.name if disbursement_id.partner_id else ""
    #         context['address_branch'] = disbursement_id.partner_id.street if disbursement_id.partner_id else ""
    #         context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #         context['company_address'] = disbursement_id.company_id.street if disbursement_id.company_id else ""
    #         total_amount = 0
    #         description_line = ""
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "USD":
    #                 total_amount += line.value
    #                 if description_line == "":
    #                     description_line += check(line.description)
    #                 else:
    #                     description_line += ", " + check(line.description)
    #         context['amount'] = "{:,.2f}".format(total_amount)
    #         context[
    #             'description'] = description_line
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Lệnh chuyển tiền BIDV
    # def lenh_chuyen_tien_bidv(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'lenh_chuyen_tien.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         total_amount = 0
    #         description = ""
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.partner_id.id == disbursement_dt_id.partner_id.id:
    #                 total_amount += line.value
    #                 if description == "":
    #                     description += check(line.description)
    #                 else:
    #                     description += ", " + check(line.description)
    #
    #         context['currency'] = check(disbursement_dt_id.currency_id.name)
    #
    #         if disbursement_dt_id.currency_id.name == 'VND':
    #             context['amount_text'] = self.get_amount_text_vnd(total_amount)
    #             context['amount'] = "{:,.0f}".format(total_amount)
    #         else:
    #             context['amount_text'] = self.get_amount_to_word(total_amount)
    #             context['amount'] = "{:,.2f}".format(total_amount)
    #
    #         context['company_address'] = disbursement_id.company_id.street if disbursement_id.company_id else ""
    #         context['company_name'] = disbursement_id.company_id.name if disbursement_id.company_id else ""
    #         context['acc_company'] = self.get_account_number_company(
    #             disbursement_id.company_id) if disbursement_id.company_id else ""
    #         beneficiary_bank = ''
    #         if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #             beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 beneficiary_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         else:
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         context['beneficiary_bank'] = check(beneficiary_bank)
    #         context['bene_bank_add'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #         # context['beneficiary'] = RichText()
    #         context['beneficiary'].add(disbursement_dt_id.partner_id.name.strip(), size=17, font='Times New Roman', italic=True, bold=True)
    #         context['acc_number'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #         context['beneficiary_add'] = check(disbursement_dt_id.partner_id.street)
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         context[
    #             'description'] = description
    #         context[
    #             'swift'] = check(disbursement_dt_id.beneficiary_bank_id.x_swift_bank)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Ủy nhiệm chi BIDV
    # def uy_nhiem_chi_bidv(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'uy_nhiem_chi.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #         context['branch_name'] = check(disbursement_id.payment_account_id.bank_id.name)
    #         context['partner_name'] = check(disbursement_dt_id.partner_id.name).strip()
    #         context['acc_partner_benficiary'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #         partner_bank = ''
    #         if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #             partner_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 partner_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         else:
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 partner_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         context['partner_bank'] = check(partner_bank)
    #         context['amount'] = "{:,.0f}".format(disbursement_dt_id.value_natural_currency)
    #         context['amount_text'] = self.get_amount_text_vnd_no_currency(disbursement_dt_id.value_natural_currency)
    #         context['description'] = check(disbursement_dt_id.description)
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         context['branch_payment'] = check(disbursement_id.payment_account_id.x_branch_bank)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Đơn xin nợ chứng từ VCB

    # Cam kết trả chứng từ VCB
    # def cam_ket_tra_chung_tu_vcb(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "cam_ket_tra_chung_tu_vcb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['vendor'] = check(disbursement_dt_id.partner_id.name).strip()
    #         context['curency_name'] = check(disbursement_dt_id.currency_id.name)
    #         if disbursement_dt_id.currency_id.name == 'VND':
    #             context['amount'] = "{:,.0f}".format(disbursement_dt_id.value)
    #             context['amount_text'] = self.get_amount_text_vnd(disbursement_dt_id.value)
    #         else:
    #             context['amount'] = "{:,.2f}".format(disbursement_dt_id.value)
    #             context['amount_text'] = self.get_amount_to_word(disbursement_dt_id.value)
    #         context['contract_code'] = check(disbursement_dt_id.origin)
    #         for line in disbursement_dt_id.purchase_order_ids:
    #             if line.date_approve:
    #                 context['sign_day'] = convert_date(line.date_approve)
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy nhận nợ VCB

    # def giay_nhan_no_vcb(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "giay_nhan_no_vcb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #         context['date_accept'] = convert_date(
    #             disbursement_id.order_id.date_confirmed) if disbursement_id.order_id.date_confirmed else ""
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['duration'] = check(disbursement_id.loan_duration)
    #         context['amount_contract'] = "{:,.0f}".format(
    #             disbursement_id.order_id.loan_amount) if disbursement_id.order_id.loan_amount else ""
    #         context['currency'] = check(disbursement_id.order_id.currency_id.name)
    #         context['authorized_person'] = check(disbursement_id.authorized_person).strip()
    #         context['authorization_letter'] = check(disbursement_id.authorization_letter).strip()
    #         context['authorized_date'] = convert_date(disbursement_id.authorized_date)
    #         total_amount = 0
    #         currency_line = ""
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if currency_line == "":
    #                 currency_line = line.currency_id.name
    #             if currency_line == "VND":
    #                 context['total_amount'] = "{:,.0f}".format(
    #                     disbursement_id.amount) if disbursement_id.amount else ""
    #                 context['total_am_text'] = self.get_amount_text_vnd(
    #                     disbursement_id.amount) if disbursement_id.amount else ""
    #                 break
    #             elif currency_line == "USD" and line.currency_id.name == "USD":
    #                 total_amount += line.value
    #
    #         context['amount_text'] = self.get_amount_text_vnd(
    #             disbursement_id.order_id.loan_amount) if disbursement_id.order_id else ""
    #
    #         context['total_currency'] = check(currency_line)
    #         if currency_line == 'USD':
    #             context['total_amount'] = "{:,.2f}".format(total_amount)
    #             context['total_am_text'] = self.get_amount_to_word(total_amount)
    #         description = ""
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if description == "":
    #                 description += check(line.description)
    #             elif line.description:
    #                 description += ", " + check(line.description)
    #
    #         context['description'] = description
    #         context['amount'] = "{:,.2f}".format(disbursement_id.amount)
    #         context['amount_text_2'] = self.get_amount_text_vnd(
    #             disbursement_id.amount) if disbursement_id.amount else ""
    #         context['description'] = description
    #         context['rate_type'] = check(disbursement_id.order_id.interest_rate_type_id.flat_rate)
    #         context['rate_period'] = ''
    #         if check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'week':
    #             context['rate_period'] = 'tuần'
    #         elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'month':
    #             context['rate_period'] = 'tháng'
    #         elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'year':
    #             context['rate_period'] = 'năm'
    #         else:
    #             context['rate_period'] = ''
    #         if disbursement_id.order_id.expiry_interest_rate_type_id:
    #             # if disbursement_id.order_id.expiry_interest_rate_type_id.type == 'flat':
    #             #     type = "Lãi suất Cố định"
    #             # elif disbursement_id.order_id.expiry_interest_rate_type_id.type == 'floating':
    #             #     type = "Lãi suất Thả nổi"
    #             # else:
    #             #     type = ""
    #             name = disbursement_id.order_id.expiry_interest_rate_type_id.name if disbursement_id.order_id.expiry_interest_rate_type_id.name else ""
    #             context['expiry_interest_rate_type'] = check(name)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy đề nghị mua ngoại tệ VCB
    # def giay_de_nghi_mua_ngoai_te_vcb(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "giay_de_nghi_mua_ngoai_te_vcb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         contract_code = ""
    #         total_amount = 0
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "USD":
    #                 total_amount += line.value
    #                 if contract_code == "":
    #                     contract_code += check(line.origin)
    #                 elif line.origin:
    #                     contract_code += ", " + check(line.origin)
    #         context['amount_usd'] = "{:,.2f}".format(total_amount)
    #         context['amount_text'] = self.get_amount_to_word(total_amount)
    #         context['contract_code'] = contract_code
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Lệnh chuyển tiền VCB
    # def lenh_chuyen_tien_vcb(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "lenh_chuyen_tien_vcb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         total_amount = 0
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.partner_id.id == disbursement_dt_id.partner_id.id:
    #                 total_amount += line.value
    #         context['currency'] = check(disbursement_dt_id.currency_id.name)
    #         if context['currency'] == 'VND':
    #             context['amount'] = "{:,.0f}".format(total_amount)
    #             context['amount_text'] = self.get_amount_text_vnd(total_amount)
    #         else:
    #             context['amount'] = "{:,.2f}".format(total_amount)
    #             context['amount_text'] = self.get_amount_to_word(total_amount)
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #         bank_partner = ''
    #         if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #             bank_partner += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 bank_partner += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         else:
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 bank_partner += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         context['bank_partner'] = check(bank_partner)
    #         context['bank_partner_add'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #         context['beneficiary'] = check(disbursement_dt_id.partner_id.name).strip()
    #         context['beneficiary_address'] = check(disbursement_dt_id.partner_id.street)
    #         context['acc_bank_partner'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #         context['bank_partner_code'] = check(disbursement_dt_id.beneficiary_bank_id.x_swift_bank)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Lệnh chuyển tiền VCB
    # def hop_dong_mua_ban_ngoai_te_vcb(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "hop_dong_mua_ban_ngoai_te_vcb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['branch_name_upper'] = check(disbursement_id.partner_id.name).strip().upper()
    #         context['branch_address'] = check(disbursement_id.partner_id.street).strip()
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         total_amount = 0
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "USD":
    #                 total_amount += line.value
    #         context['amount'] = "{:,.2f}".format(total_amount)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Ủy nhiệm chi VCB
    # def uy_nhiem_chi_vcb(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'uy_nhiem_chi_vcb.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #         context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #         context['branch_name'] = check(disbursement_id.payment_account_id.bank_id.name)
    #         context['partner_name'] = check(disbursement_dt_id.partner_id.name).strip()
    #         context['partner_address'] = check(disbursement_dt_id.partner_id.street)
    #         context['acc_partner_benficiary'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #         partner_bank = ''
    #         if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #             partner_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 partner_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         else:
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 partner_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         context['partner_bank'] = check(partner_bank)
    #         context['amount'] = "{:,.0f}".format(disbursement_dt_id.value_natural_currency)
    #         context['amount_text'] = self.get_amount_text_vnd_no_currency(disbursement_dt_id.value_natural_currency)
    #         context['description'] = check(disbursement_dt_id.description)
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         context['branch_payment'] = check(disbursement_id.payment_account_id.x_branch_bank)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy đề nghị mua ngoại tệ VTB
    # def de_nghi_mua_ngoai_te_vtb(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "de_nghi_mua_ngoai_te_vtb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #         context['bank_acc'] = self.get_bank_name_partner(disbursement_id.partner_id)
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         description_line = ""
    #         total_amount = 0
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "USD":
    #                 total_amount += line.value
    #                 if description_line == "":
    #                     description_line += check(line.description)
    #                 elif line.description:
    #                     description_line += ", " + check(line.description)
    #         context['description'] = check(description_line)
    #         context['amount'] = "{:,.2f}".format(total_amount)
    #         context['amount_text'] = self.get_amount_to_word(total_amount)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Lệnh chuyển tiền VTB
    # def lenh_chuyen_tien_vtb(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "lenh_chuyen_tien_vtb.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #
    #         total_amount = 0
    #         description = ""
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.partner_id.id == disbursement_dt_id.partner_id.id:
    #                 total_amount += line.value
    #                 if description == "":
    #                     description += check(line.description)
    #                 elif line.description:
    #                     description += ", " + line.description
    #
    #         context['currency'] = check(disbursement_dt_id.currency_id.name)
    #         if context['currency'] == 'VND':
    #             context['amount'] = "{:,.0f}".format(total_amount)
    #             context['amount_text'] = self.get_amount_text_vnd(total_amount)
    #         else:
    #             context['amount'] = "{:,.2f}".format(total_amount)
    #             context['amount_text'] = self.get_amount_to_word(total_amount)
    #
    #         context['description'] = check(description)
    #         beneficiary_bank = ''
    #         if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #             beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 beneficiary_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         else:
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 beneficiary_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         context['beneficiary_bank'] = check(beneficiary_bank)
    #         context['bene_bank_add'] = check(disbursement_dt_id.beneficiary_bank_id.bank_id.street)
    #         context['beneficiary'] = check(disbursement_dt_id.partner_id.name).strip()
    #         context['acc_number'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #         context['beneficiary_add'] = check(disbursement_dt_id.partner_id.street)
    #         context['bank_code'] = check(disbursement_dt_id.beneficiary_bank_id.x_swift_bank)
    #
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy nhận nợ USD VTB
    # def giay_nhan_no_vtb_usd(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "giay_nhan_no_vtb_usd.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #         context['date_contract'] = convert_date(
    #             disbursement_id.order_id.date_confirmed) if disbursement_id.order_id.date_confirmed else ""
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['branch_upper'] = check(disbursement_id.partner_id.name.upper())
    #         context['amount_contract'] = "{:,.0f}".format(
    #             disbursement_id.order_id.loan_amount) if disbursement_id.order_id else ""
    #         context['bank_acc_partner'] = self.get_bank_name_partner(disbursement_id.partner_id)
    #         context['authorized_date'] = convert_date(
    #             disbursement_id.authorized_date) if disbursement_id.authorized_date else "........................................"
    #         context[
    #             'authorized_person'] = disbursement_id.authorized_person.strip() if disbursement_id.authorized_person else "........................................"
    #         context['authorization_letter'] = check(disbursement_id.authorization_letter).strip()
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #
    #         total_no = 0
    #         total_amount = 0
    #         contract_code = ""
    #         description_line = ""
    #         table_list_data = []
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "USD" and line.x_type == "invoice":
    #                 infor = {}
    #                 # Tong tien o cac don hang
    #                 total_invoice = 0
    #                 contract_code = ""
    #                 for item in line.invoice_ids:
    #                     if item.currency_id.name == 'USD':
    #                         total_invoice += item.amount_total
    #                     if contract_code == "":
    #                         contract_code += check(item.x_number_invoice)
    #                     else:
    #                         contract_code += ", " + check(item.x_number_invoice)
    #                 # Mo ta cua cac line
    #                 if description_line == "":
    #                     description_line += check(line.description)
    #                 elif line.description:
    #                     description_line += ", " + check(line.description)
    #                 # Tong tien cac lan thanh toan
    #                 total_no += line.value
    #                 infor['amount'] = "{:,.2f}".format(total_invoice)
    #                 infor['amount_no'] = "{:,.2f}".format(line.value)
    #                 total_amount += total_invoice
    #                 infor['partner_name'] = line.partner_id.name
    #                 infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                 if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                     infor['bank_name'] = check(
    #                         line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                         line.beneficiary_bank_id.x_branch_bank).strip()
    #                 elif not line.beneficiary_bank_id.x_branch_bank:
    #                     infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                 infor['contract_code'] = check(contract_code)
    #                 infor['contract_date'] = convert_date(line.create_date)
    #                 table_list_data.append(infor)
    #             elif line.currency_id.name == "USD":
    #                 infor = {}
    #                 # Tong tien o cac don hang
    #                 total_purchase = 0
    #                 for item in line.purchase_order_ids:
    #                     if item.currency_id.name == 'USD':
    #                         total_purchase += item.amount_total
    #
    #                 # Mo ta cua cac line
    #                 if description_line == "":
    #                     description_line += check(line.description)
    #                 elif line.description:
    #                     description_line += ", " + check(line.description)
    #
    #                 # Tong tien cac lan thanh toan
    #                 total_no += line.value
    #                 infor['amount'] = "{:,.2f}".format(total_purchase)
    #                 infor['amount_no'] = "{:,.2f}".format(line.value)
    #                 total_amount += total_purchase
    #                 infor['partner_name'] = line.partner_id.name
    #                 infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                 bank_name = ''
    #                 if line.beneficiary_bank_id.bank_id.name:
    #                     bank_name += check(line.beneficiary_bank_id.bank_id.name).strip()
    #                     if line.beneficiary_bank_id.x_branch_bank:
    #                         bank_name += " - " + check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                 else:
    #                     if line.beneficiary_bank_id.x_branch_bank:
    #                         bank_name += check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                 infor['bank_name'] = check(bank_name)
    #                 infor['contract_code'] = check(line.origin)
    #                 infor['contract_date'] = convert_date(line.create_date)
    #                 if contract_code == "":
    #                     contract_code += check(line.origin)
    #                 elif line.origin:
    #                     contract_code += ", " + check(line.origin)
    #                 table_list_data.append(infor)
    #
    #         context['description'] = description_line
    #         context['list_data'] = table_list_data
    #         context['total_amount'] = "{:,.2f}".format(total_amount)
    #         context['total_no'] = "{:,.2f}".format(total_no)
    #         context['rate_type'] = check(disbursement_id.order_id.interest_rate_type_id.flat_rate)
    #         context['rate_period'] = ''
    #         if check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'week':
    #             context['rate_period'] = 'Mỗi tuần'
    #         elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'month':
    #             context['rate_period'] = 'Mỗi tháng'
    #         elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'year':
    #             context['rate_period'] = 'Mỗi năm'
    #         else:
    #             context['rate_period'] = ''
    #         if disbursement_id.order_id.expiry_interest_rate_type_id:
    #             name = disbursement_id.order_id.expiry_interest_rate_type_id.name if disbursement_id.order_id.expiry_interest_rate_type_id.name else ""
    #             # if disbursement_id.order_id.expiry_interest_rate_type_id.type == 'flat':
    #             #     type = "Lãi suất Cố định"
    #             # elif disbursement_id.order_id.expiry_interest_rate_type_id.type == 'floating':
    #             #     type = "Lãi suất Thả nổi"
    #             # else:
    #             #     type = ""
    #             context['expiry_interest_rate_type'] = check(name)
    #
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Giấy nhận nợ VND VTB
    # def giay_nhan_no_vtb_vnd(self, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', "giay_nhan_no_vtb_vnd.docx")], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['number_contract'] = check(disbursement_id.order_id.loan_number)
    #         context['date_contract'] = convert_date(
    #             disbursement_id.order_id.date_confirmed) if disbursement_id.order_id.date_confirmed else ""
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['branch_name'] = check(disbursement_id.partner_id.name).strip()
    #         context['branch_upper'] = check(disbursement_id.partner_id.name.upper())
    #         context['amount_contract'] = "{:,.0f}".format(
    #             disbursement_id.order_id.loan_amount) if disbursement_id.order_id else ""
    #         context['bank_acc_partner'] = self.get_bank_name_partner(disbursement_id.partner_id)
    #         context['authorized_date'] = convert_date(
    #             disbursement_id.authorized_date) if disbursement_id.authorized_date else "........................................"
    #         context['authorized_person'] = disbursement_id.authorized_person.strip() if disbursement_id.authorized_person else "................................................"
    #         context['authorization_letter'] = check(disbursement_id.authorization_letter).strip()
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         total_no = 0
    #         total_amount = 0
    #         contract_code = ""
    #         description_line = ""
    #         table_list_data = []
    #         for line in disbursement_id.disbursement_dt_ids:
    #             if line.currency_id.name == "VND" and line.x_type == "invoice":
    #                 infor = {}
    #                 # Tong tien o cac don hang
    #                 contract_code = ""
    #                 total_invoice = 0
    #                 for item in line.invoice_ids:
    #                     if item.currency_id.name == 'VND':
    #                         total_invoice += item.amount_total
    #                     if contract_code == "":
    #                         contract_code += check(item.x_number_invoice)
    #                     else:
    #                         contract_code += ", " + check(item.x_number_invoice)
    #                 # Mo ta cua cac line
    #                 if description_line == "":
    #                     description_line += check(line.description)
    #                 elif line.description:
    #                     description_line += ", " + check(line.description)
    #                 # Tong tien cac lan thanh toan
    #                 total_no += line.value
    #                 infor['amount'] = "{:,.0f}".format(total_invoice)
    #                 infor['amount_no'] = "{:,.0f}".format(line.value)
    #                 total_amount += total_invoice
    #                 infor['partner_name'] = line.partner_id.name
    #                 infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                 if line.beneficiary_bank_id.x_branch_bank and line.beneficiary_bank_id.bank_id.name:
    #                     infor['bank_name'] = check(
    #                         line.beneficiary_bank_id.bank_id.name).strip() + " - " + check(
    #                         line.beneficiary_bank_id.x_branch_bank).strip()
    #                 elif not line.beneficiary_bank_id.x_branch_bank:
    #                     infor['bank_name'] = check(line.beneficiary_bank_id.bank_id.name).strip()
    #                 infor['contract_code'] = check(contract_code)
    #                 infor['contract_date'] = convert_date(line.create_date)
    #                 table_list_data.append(infor)
    #             elif line.currency_id.name == "VND":
    #                 infor = {}
    #                 # Tong tien o cac don hang
    #                 total_purchase = 0
    #                 for item in line.purchase_order_ids:
    #                     if item.currency_id.name == 'VND':
    #                         total_purchase += item.amount_total
    #
    #                 # Mo ta cua cac line
    #                 if description_line == "":
    #                     description_line += check(line.description)
    #                 elif line.description:
    #                     description_line += ", " + check(line.description)
    #
    #                 # Tong tien cac lan thanh toan
    #                 total_no += line.value
    #                 infor['amount'] = "{:,.0f}".format(total_purchase)
    #                 infor['amount_no'] = "{:,.0f}".format(line.value)
    #                 total_amount += total_purchase
    #                 infor['partner_name'] = line.partner_id.name
    #                 infor['acc_number'] = check(line.beneficiary_bank_id.acc_number)
    #                 bank_name = ''
    #                 if line.beneficiary_bank_id.bank_id.name:
    #                     bank_name += check(line.beneficiary_bank_id.bank_id.name).strip()
    #                     if line.beneficiary_bank_id.x_branch_bank:
    #                         bank_name += " - " + check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                 else:
    #                     if line.beneficiary_bank_id.x_branch_bank:
    #                         bank_name += check(line.beneficiary_bank_id.x_branch_bank).strip()
    #                 infor['bank_name'] = check(bank_name)
    #                 infor['contract_code'] = check(line.origin)
    #                 infor['contract_date'] = convert_date(line.create_date)
    #                 if contract_code == "":
    #                     contract_code += check(line.origin)
    #                 elif line.origin:
    #                     contract_code += ", " + check(line.origin)
    #                 table_list_data.append(infor)
    #
    #         context['description'] = description_line
    #         context['list_data'] = table_list_data
    #         context['total_amount'] = "{:,.0f}".format(total_amount)
    #         context['total_no'] = "{:,.0f}".format(total_no)
    #         context['amount_text'] = self.get_amount_text_vnd(total_no)
    #         context['rate_type'] = check(disbursement_id.order_id.interest_rate_type_id.flat_rate)
    #         context['rate_period'] = ''
    #         if check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'week':
    #             context['rate_period'] = 'Mỗi tuần'
    #         elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'month':
    #             context['rate_period'] = 'Mỗi tháng'
    #         elif check(disbursement_id.order_id.interest_rate_type_id.interest_rate_period) == 'year':
    #             context['rate_period'] = 'Mỗi năm'
    #         else:
    #             context['rate_period'] = ''
    #
    #         if disbursement_id.order_id.expiry_interest_rate_type_id:
    #             name = disbursement_id.order_id.expiry_interest_rate_type_id.name if disbursement_id.order_id.expiry_interest_rate_type_id.name else ""
    #             # if disbursement_id.order_id.expiry_interest_rate_type_id.type == 'flat':
    #             #     type = "Lãi suất Cố định"
    #             # elif disbursement_id.order_id.expiry_interest_rate_type_id.type == 'floating':
    #             #     type = "Lãi suất Thả nổi"
    #             # else:
    #             #     type = ""
    #             context['expiry_interest_rate_type'] = check(name)
    #
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    # Ủy nhiệm chi VTB
    # def uy_nhiem_chi_vtb(self, disbursement_dt_id, disbursement_id):
    #     docs = self.env['word.template'].search([('file_name', '=', 'uy_nhiem_chi_vtb.docx')], limit=1)
    #     if docs:
    #         stream = BytesIO(codecs.decode(docs.file_data, "base64"))
    #         docdata = DocxTemplate(stream)
    #         context = {}
    #         context['company_name'] = check(disbursement_id.company_id.name)
    #         context['company_address'] = check(disbursement_id.company_id.street)
    #         context['acc_company'] = self.get_account_number_partner(disbursement_id.partner_id)
    #         context['branch_name'] = check(disbursement_id.payment_account_id.bank_id.name)
    #         if disbursement_id.payment_account_id.x_branch_bank:
    #             context['branch_name'] += ' - ' + disbursement_id.payment_account_id.x_branch_bank
    #         context['partner_name'] = check(disbursement_dt_id.partner_id.name).strip()
    #         context['acc_partner_benficiary'] = check(disbursement_dt_id.beneficiary_bank_id.acc_number)
    #         partner_bank = ''
    #         if disbursement_dt_id.beneficiary_bank_id.bank_id.name:
    #             partner_bank += check(disbursement_dt_id.beneficiary_bank_id.bank_id.name).strip()
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 partner_bank += " - " + check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         else:
    #             if disbursement_dt_id.beneficiary_bank_id.x_branch_bank:
    #                 partner_bank += check(disbursement_dt_id.beneficiary_bank_id.x_branch_bank).strip()
    #         context['partner_bank'] = check(partner_bank)
    #         context['amount'] = "{:,.0f}".format(disbursement_dt_id.value_natural_currency)
    #         context['amount_text'] = self.get_amount_text_vnd_no_currency(disbursement_dt_id.value_natural_currency)
    #         context['description'] = check(disbursement_dt_id.description)
    #         context['account_payment'] = check(disbursement_id.payment_account_id.acc_number)
    #         docdata.render(context)
    #         tempFile = NamedTemporaryFile(delete=False)
    #         docdata.save(tempFile)
    #         tempFile.flush()
    #         tempFile.close()
    #         return tempFile
    #     return None

    def action_disbursement_register_wizard(self):
        disbursement_ids = self.filtered(lambda l:l.state == 'confirmed')
        action = self.env.ref(self._get_disbursement_payment_action_xml_id()).read()[0]
        ctx = ast.literal_eval(action['context'])
        ctx.update({'default_disbursement_ids': disbursement_ids.ids,'default_order_id': self.order_id.id})
        if self.is_compute_by_dt:
            ctx.update({'default_disbursement_ids': disbursement_ids.ids,'default_order_id': self.order_id.id,'default_line_ids': self.disbursement_dt_ids.filtered(lambda x: len(x.purchase_order_ids) > 0 or len(x.lc_ids) > 0 or len(x.invoice_ids) > 0).ids})
        action['context'] = ctx
        return action

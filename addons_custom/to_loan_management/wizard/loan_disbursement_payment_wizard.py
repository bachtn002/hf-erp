from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, format_amount
import ast


class AbstractLoanDisbursementPaymentWizard(models.AbstractModel):
    _name = 'abstract.loan.disbursement.payment.wizard'
    _inherit = 'abstract.loan.payment'
    _description = 'Loan Disbursement Payment Wizard Abstract'

    company_id = fields.Many2one(compute='_compute_company', store=True)
    order_id = fields.Many2one('loan.borrowing.order', string='Contract', required=True,
                               readonly=True,
                               help="The Borrowing Loan contract that the disbursement follows")
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type',
                                    default='outbound')

    disbursement_method = fields.Selection([('beneficiary', 'Beneficiary'), ('in_bank', 'In Bank')],
                                           default='beneficiary', string='Disbursement Method')

    line_ids = fields.One2many('loan.borrow.disbursement.dt', 'loan_borrow_disbursement_payment_wizard_id',
                               'Loan Borrow Disbursement Detail')


    @api.constrains('disbursement_ids')
    def _check_disbursement_ids(self):
        for r in self:
            company_id = r.disbursement_ids.mapped('company_id')
            if len(company_id) > 1:
                raise ValidationError(_("You cannot make payment for disbursements to multiple companies at once"))
            if self.company_id and self.company_id.id != company_id.id:
                raise ValidationError(_("The payment is for the company '%s' while the matched disbursement(s) belongs to another company (%s)")
                                      % (self.company_id.name, company_id.name))
            partner_id = r.disbursement_ids.mapped('partner_id')
            if len(partner_id) > 1:
                raise ValidationError(_("You cannot make payment for the disbursements that concerning multiple partners"))
            currency_id = r.disbursement_ids.mapped('currency_id')
            if len(currency_id) > 1:
                raise ValidationError(_("You cannot make payment for the disbursements that are in different currencies at once"))

    @api.constrains('disbursement_ids', 'amount')
    def _check_amount_vs_disbursements(self):
        for r in self:
            if not r.disbursement_ids:
                continue

            remaining_amt = r._calculate_remaining_amount()
            if float_compare(r.amount, remaining_amt, precision_rounding=r.currency_id.rounding) == 1:
                raise ValidationError(_("Payment Amount should not be greater than the total remaining amount of the selected disbursement(s)"))

    @api.depends('disbursement_ids.company_id')
    def _compute_company(self):
        for r in self:
            r.company_id = r.disbursement_ids[0].company_id if r.disbursement_ids else False

    def _get_default_disbursements(self):
        active_ids = self.env.context.get('active_ids', [])
        return self.disbursement_ids.search([('id', 'in', active_ids)])

    def _calculate_remaining_amount(self):
        remaining_amt = 0.0
        if self.disbursement_ids:
            remaining_amt = sum(self.disbursement_ids.mapped('to_receive_amount'))
        return remaining_amt

    def _onchange_disbursement_ids(self):
        res = {}
        self.amount = self._calculate_remaining_amount()
        self.communication = ", ".join(self.disbursement_ids.mapped('name'))
        self.partner_id = self.disbursement_ids[0].partner_id if self.disbursement_ids else False
        currency_ids = self.disbursement_ids.mapped('currency_id')
        journal_id_domain = [('type', 'in', ('bank', 'cash'))]
        if currency_ids:
            if any(currency_id.id == self.company_id.currency_id.id for currency_id in currency_ids):
                journal_id_domain += ['|', ('currency_id', '=', False), ('currency_id', 'in', currency_ids.ids)]
            else:
                journal_id_domain += [('currency_id', 'in', currency_ids.ids)]
        res['domain'] = {'journal_id':journal_id_domain}
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.disbursement_ids = self.disbursement_ids.search([('partner_id', '=', self.partner_id.id), ('state', '=', 'confirmed')])

    def _get_loan_account(self):
        return self._get_disbursements()[0].account_id


    def action_payment_create_and_match(self):
        self.ensure_one()
        if self.disbursement_method == 'in_bank':
            payment_id = self.env['loan.disbursement.payment'].create(self._prepare_payment_data())
            self.disbursement_ids.match_payments(payment_id)
            if payment_id.state == 'matched':
                payment_id.action_post()
        elif self.disbursement_method == 'beneficiary':
            # amount_payment = sum(x.value * x.rate  for x in self.line_ids)
            # if  amount_payment > self.amount:
            #     raise ValidationError(
            #         _("the payment amount for the contracts must be less than or equal to this disbursement"))

            for line in self.line_ids.filtered(lambda o: o.x_payment_type == 'pay'):
                val_line = []
                total_amount = 0
                for x in self.disbursement_ids.filtered(lambda a: a.paid_amount < a.amount):
                    total_amount += x.amount - x.paid_amount
                    if total_amount > line.value_natural_currency:
                        val_line.append((0,0,{
                            'disbursement_id': x.id,
                            'order_id': self.order_id.id,
                            'matched_amount': line.value_natural_currency
                        }))
                        break
                    elif total_amount < line.value_natural_currency:
                        val_line.append((0,0,{
                            'disbursement_id': x.id,
                            'order_id': self.order_id.id,
                            'matched_amount': x.amount - x.paid_amount
                        }))
                    else:
                        val_line.append((0,0,{
                            'disbursement_id': x.id,
                            'order_id': self.order_id.id,
                            'matched_amount': x.amount - x.paid_amount
                        }))
                        break
                vals = {
                    # 'name': self.journal_id.sequence.next_by_id(sequence_date=self.payment_date),
                    'partner_type': self.partner_type,
                    'partner_id': self.partner_id.id,
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id,
                    'payment_method_id': self.payment_method_id.id,
                    'amount': line.value_natural_currency,
                    'currency_id': self.currency_id.id,
                    'payment_date': self.payment_date,
                    'communication': self.communication,
                    'state': 'draft',
                    'beneficiary_bank_id': line.beneficiary_bank_id.id,
                    'description': line.description,
                    'purchase_order_ids': [[4, b] for b in line.purchase_order_ids.ids],
                    'invoice_ids': [[4, c] for c in line.invoice_ids.ids],
                    'loan_borrow_disbursement_payment_match_ids': val_line,

                }
                payment_id = self.env['loan.disbursement.payment'].create(vals)
                move_id = line.create_payment_move()
                move_id.action_post()
                if line.x_type == 'contract':
                    invoice_lines = line.purchase_order_ids.mapped('order_line.invoice_lines.move_id').filtered(lambda inv: inv.state == 'posted' and inv.amount_residual > 0)
                else:
                    invoice_lines = line.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.amount_residual > 0)
                move_line_debit = self.env['account.move.line'].search(
                    [('move_id', '=', move_id.id), ('debit', '>', 0),
                     ('parent_state', '=', 'posted'), ('account_internal_type', '=', 'payable'),
                     ('reconciled', '=', False),
                     ('amount_residual', '>', 0)], limit=1)
                if move_line_debit:

                    for invoice in invoice_lines:
                        if move_line_debit.amount_residual > 0:
                            invoice.js_assign_outstanding_line(move_line_debit.id)
                    lst_js_assign_outstanding_line = []
                    for invoice in invoice_lines:
                        if move_line_debit.amount_residual > 0:
                            destination_account_ids = invoice.mapped(
                                'line_ids.account_id').filtered(
                                lambda account: account.user_type_id.type in ('receivable', 'payable'))
                            # Truong hop thanh toan cho thue se co nhieu tai khoan thanh toan khac nhau => phai tach move_line theo cac tai khoan thanh toan

                            for destination_account_id in destination_account_ids:

                                if invoice.amount_residual > invoice.amount_total:
                                    invoice_amount_residual = invoice.amount_total - (invoice.amount_residual - invoice.amount_total)
                                else:
                                    invoice_amount_residual = invoice.amount_residual
                                if move_line_debit.account_id != destination_account_id and move_line_debit.account_id == move_id.partner_id.property_account_payable_id and move_line_debit.amount_residual > 0:
                                    if move_line_debit.amount_residual > invoice_amount_residual:
                                        move_line_debit.move_id.button_draft()
                                        move_line_debit.with_context(check_move_validity=False).write({'debit' : move_line_debit.debit - invoice_amount_residual})
                                        move_rcl_debit = move_line_debit.with_context(check_move_validity=False).copy({'account_id': destination_account_id.id, 'debit' :invoice_amount_residual})
                                        move_line_debit.move_id.post()
                                        lst_js_assign_outstanding_line.append([invoice.id,move_rcl_debit.id])
                                    else:
                                        move_line_debit.move_id.button_draft()
                                        move_line_debit.with_context(check_move_validity=False).write({'account_id': destination_account_id.id})
                                        move_line_debit.move_id.post()
                                        lst_js_assign_outstanding_line.append([invoice.id, move_line_debit.id])
                    for rcl in lst_js_assign_outstanding_line:
                        inv = self.env['account.move'].browse(rcl[0])
                        inv.js_assign_outstanding_line(rcl[1])
                payment_id.write({'move_id': move_id.id, 'state': 'posted'})

            for line in self.line_ids.filtered(lambda m: m.x_payment_type == 'deposit'):
                val_line = []
                total_amount = 0
                for z in self.disbursement_ids.filtered(lambda a: a.paid_amount < a.amount):
                    total_amount += z.amount - z.paid_amount
                    if total_amount > line.value_natural_currency:
                        val_line.append((0,0,{
                            'disbursement_id': z.id,
                            'order_id': self.order_id.id,
                            'matched_amount':line.value_natural_currency
                        }))
                        break
                    elif total_amount < line.value_natural_currency:
                        val_line.append((0,0,{
                            'disbursement_id': z.id,
                            'order_id': self.order_id.id,
                            'matched_amount': z.amount - z.paid_amount
                        }))
                    else:
                        val_line.append((0,0,{
                            'disbursement_id': z.id,
                            'order_id': self.order_id.id,
                            'matched_amount': z.amount - z.paid_amount
                        }))
                        break

                vals = {
                    'name': self.journal_id.sequence_id.next_by_id(sequence_date=self.payment_date),
                    'partner_type': self.partner_type,
                    'partner_id': self.partner_id.id,
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id,
                    'payment_method_id': self.payment_method_id.id,
                    'amount': line.value_natural_currency,
                    'currency_id': self.currency_id.id,
                    'payment_date': self.payment_date,
                    'communication': self.communication,
                    'state': 'draft',
                    'beneficiary_bank_id': line.beneficiary_bank_id.id,
                    'description': line.description,
                    'purchase_order_ids': [[4, k] for k in line.purchase_order_ids.ids],
                    'invoice_ids': [[4, l] for l in line.invoice_ids.ids],
                    'loan_borrow_disbursement_payment_match_ids': val_line,

                }
                payment_id = self.env['loan.disbursement.payment'].create(vals)
                move_id = line.create_payment_move()
                move_id.action_post()

                payment_id.write({'move_id': move_id.id, 'state': 'posted'})

        for x in self.disbursement_ids:
            if x.to_receive_amount <= 0 and x.state not in ('paid','refunded','cancelled'):
                x.write({
                    'state': 'paid',
                })

    @api.onchange('amount')
    def _onchange_amount(self):
        order_ids = self.disbursement_ids.mapped('order_id')
        while float_compare(self.amount, sum(self.mapped('disbursement_ids.to_receive_amount')), precision_rounding=self.currency_id.rounding) == 1:
            remain_disbursement_ids = order_ids.mapped('disbursement_line_ids').filtered(lambda l: l.id not in self.disbursement_ids.ids and l.state == 'confirmed')
            if not remain_disbursement_ids:
                break
            self.disbursement_ids += remain_disbursement_ids[0]


class LoanBorrowDisbursementPaymentWizard(models.Model):
    # _name = 'loan.borrow.disbursement.payment.wizard'
    _name = 'loan.borrow.disbursement.payment.wizard'
    _inherit = 'abstract.loan.disbursement.payment.wizard'
    _description = 'Loan Borrow Disbursement Payment Wizard'

    disbursement_ids = fields.Many2many('loan.borrow.disbursement', 'loan_borrow_disbursement_payment_wizard_rel', 'wizard_id', 'disbursement_id',
                                        string='Disbursements',
                                        default=lambda self: self._get_default_disbursements())
    disbursement_method = fields.Selection([('beneficiary', 'Beneficiary'), ('in_bank', 'In Bank')],
                                           default='beneficiary', string='Disbursement Method')
    line_ids = fields.One2many('loan.borrow.disbursement.dt', 'loan_borrow_disbursement_payment_wizard_id', 'Loan Borrow Disbursement Detail')

    @api.constrains('line_ids','disbursement_method')
    def _check_line_ids(self):
        for item in self:
            if item.disbursement_method == 'beneficiary' and len(item.line_ids) == 0:
                raise UserError(_('Warning'), ('You must create a Payment with disbursement method beneficiary'))


    @api.onchange('disbursement_ids')
    def _onchange_disbursement_ids(self):
        super(LoanBorrowDisbursementPaymentWizard, self)._onchange_disbursement_ids()

    @api.onchange('line_ids','disbursement_method')
    def onchange_line_ids(self):
        if self.disbursement_method == 'beneficiary':
            self.amount = sum(float_round(x.value * x.rate, precision_rounding=self.currency_id.rounding) for x in self.line_ids)
        else:
            # self.amount = sum(x.currency_id._convert(x.amount - x.paid_amount, self.currency_id, self.company_id, self.payment_date or fields.Date.today()) for x in self.disbursement_ids)
            self.amount = sum(x.currency_id._convert(x.amount - x.paid_amount, self.currency_id, self.company_id,  self.payment_date or fields.Date.today()) for x in self.disbursement_ids)

class LoanLendDisbursementPaymentWizard(models.TransientModel):
    _name = 'loan.lend.disbursement.payment.wizard'
    _inherit = 'abstract.loan.disbursement.payment.wizard'
    _description = 'Loan Lend Disbursement Payment Wizard'

    disbursement_ids = fields.Many2many('loan.lend.disbursement', 'loan_lend_disbursement_payment_wizard_rel', 'wizard_id', 'disbursement_id',
                                        string='Disbursements',
                                        default=lambda self: self._get_default_disbursements())

    @api.onchange('disbursement_ids')
    def _onchange_disbursement_ids(self):
        super(LoanLendDisbursementPaymentWizard, self)._onchange_disbursement_ids()


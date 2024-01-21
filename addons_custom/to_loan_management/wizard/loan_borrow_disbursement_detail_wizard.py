from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare, float_round, float_is_zero, format_amount


class LoanBorrowDisbursementDetailWizard(models.Model):
    _name = 'loan.borrow.disbursement.dt'
    _description = 'Disbursement Plan Line'

    loan_borrow_disbursement_payment_wizard_id = fields.Many2one('loan.borrow.disbursement.payment.wizard', 'Loan Borrow Disbursement Payment Wizard')
    x_payment_type = fields.Selection([('deposit', 'Deposit'), ('pay', 'Payment')], default='pay', string='Payment Type')
    x_type = fields.Selection([('contract', 'Contract'), ('invoice', 'Invoice')], default='contract', string='Type')
    partner_id = fields.Many2one('res.partner', 'Partner')
    purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Order')
    # invoice_ids = fields.Many2many('account.move','loan_acc_invoice_rel', string='Invoice', domain=[('state', '=', 'posted'),('type', '=', 'in_invoice')])
    invoice_ids = fields.Many2many('account.move','loan_acc_invoice_rel', string='Invoice', domain=[('state', '=', 'posted')])
    origin = fields.Char('Contract')
    currency_id = fields.Many2one('res.currency', string='Currency')
    value = fields.Monetary('Value', required=True)
    value_natural_currency = fields.Float('Value natural currency')
    rate = fields.Float('Rate')
    destination_account_id = fields.Many2one('account.account', 'Destination account')
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type', default='outbound')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          help="If specified, when invoicing interests of this contract,"
                                               " this analytic account will be filled automatically into the invoice lines")
    object_cost_id = fields.Many2one('object.cost', string='Object Cost', ondelete='cascade')
    part_id = fields.Many2one('res.partner', string='Partner')
    order_id = fields.Many2one('loan.borrowing.order', string='Contract',
                               help="The Borrowing Loan contract that the disbursement follows")

    lc_ids = fields.Many2many('stock.landed.cost', string='LC',
                               help="The Borrowing Loan LC that the disbursement follows")
    description = fields.Char(string='Description', size=500)
    beneficiary_bank_id = fields.Many2one('res.partner.bank', string='Beneficiary Bank')
    loan_disbursement_id = fields.Many2one('loan.borrow.disbursement', string='Loan Borrow Disbursement')


    @api.constrains('x_payment_type', 'purchase_order_ids')
    def _constrains_check_contract(self):
        for item in self:
            if item.x_payment_type == 'deposit' and len(item.purchase_order_ids) >1:
                raise UserError(_("Only 1 deposit per line is allowed."))


    def create_payment_move(self):
        return self.env['account.move'].create(self._parepare_account_move_data())


    def _parepare_account_move_data(self):
        lines_data = self._prepare_acc_move_lines_data()
        return {
            'ref': ', '.join(self.purchase_order_ids.filtered(lambda a: a.origin != False ).mapped('origin')) or ', '.join(self.invoice_ids.filtered(lambda a: a.ref != False ).mapped('ref')),
            'line_ids': lines_data,
            'journal_id': self.loan_borrow_disbursement_payment_wizard_id.journal_id.id,
            'date': self.loan_borrow_disbursement_payment_wizard_id.payment_date,
            'partner_id': self.partner_id.id,
            'loan_disbursement_id': self.loan_disbursement_id.id
            }

    def _prepare_acc_move_lines_data(self):
        amount, amount_currency, diff_currency, possitive_amount = self._prepare_amounts()
        loan_account_id = self.loan_borrow_disbursement_payment_wizard_id.order_id.account_id
        debit_account_id = self.partner_id.property_account_payable_id.id
        if self.x_payment_type == 'deposit':
            if self.purchase_order_ids[0].company_id.x_account_deposit_id.id:
                debit_account_id = self.purchase_order_ids[0].company_id.x_account_deposit_id.id
                self.purchase_order_ids[0].write({'x_status_deposit': 'deposit','x_remaining_amount': abs(amount),'x_deposit_amount': abs(amount),})
            else:
                raise UserError(_("This company not yet config deposit account. Please contact with administrator."))


        # loan line
        line1 = {
            'date_maturity': self.loan_borrow_disbursement_payment_wizard_id.payment_date,
            'partner_id': self.part_id.id or self.partner_id.id,
            'name': ', '.join(self.purchase_order_ids.filtered(lambda a: a.origin != False ).mapped('origin')) or ', '.join(self.invoice_ids.filtered(lambda a: a.ref != False ).mapped('ref')),
            'date': self.loan_borrow_disbursement_payment_wizard_id.payment_date,
            'debit':-1.0 * amount if not possitive_amount else 0.0,
            'credit': amount if possitive_amount else 0.0,
            'currency_id': diff_currency and self.currency_id.id,
            # 'account_id': self.partner_id.property_account_payable_id.id,
            'account_id': debit_account_id,
            'ref': ', '.join(self.purchase_order_ids.filtered(lambda a: a.origin != False ).mapped('origin')) or ', '.join(self.invoice_ids.filtered(lambda a: a.ref != False ).mapped('ref')),
            # 'partner_id': self.part_id.id,
            # 'object_cost_id': self.object_cost_id.id,
            'analytic_account_id': self.analytic_account_id.id,
        }
        if diff_currency:
            if float_compare(line1['credit'], 0.0, precision_rounding=self.loan_borrow_disbursement_payment_wizard_id.order_id.company_id.currency_id.rounding) == 1:
                line1['amount_currency'] = -1.0 * abs(amount_currency)
            elif float_compare(line1['debit'], 0.0, precision_rounding=self.loan_borrow_disbursement_payment_wizard_id.order_id.company_id.currency_id.rounding) == 1:
                line1['amount_currency'] = abs(amount_currency)

        # loan payment line
        line2 = {
            'date_maturity': self.loan_borrow_disbursement_payment_wizard_id.payment_date,
            'partner_id': self.part_id.id or self.order_id.partner_id.id,
            'name': ', '.join(self.purchase_order_ids.filtered(lambda a: a.origin != False ).mapped('origin')) or ', '.join(self.invoice_ids.filtered(lambda a: a.ref != False ).mapped('ref')),
            'date': self.loan_borrow_disbursement_payment_wizard_id.payment_date,
            'debit': amount if possitive_amount else 0.0,
            'credit':-1.0 * amount if not possitive_amount else 0.0,
            # 'account_id': self.journal_id.default_credit_account_id.id if possitive_amount else self.journal_id.default_debit_account_id.id,
            'account_id': loan_account_id.id,
            'currency_id': diff_currency and self.currency_id.id,
            'ref': ', '.join(self.purchase_order_ids.filtered(lambda a: a.origin != False ).mapped('origin')) or ', '.join(self.invoice_ids.filtered(lambda a: a.ref != False ).mapped('ref')),
            # 'partner_id': self.part_id.id,
            # 'object_cost_id': self.object_cost_id.id,
            'analytic_account_id': self.analytic_account_id.id,
        }
        if diff_currency:
            if float_compare(line2['credit'], 0.0, precision_rounding=self.loan_borrow_disbursement_payment_wizard_id.order_id.company_id.currency_id.rounding) == 1:
                line2['amount_currency'] = -1.0 * abs(amount_currency)
            elif float_compare(line2['debit'], 0.0, precision_rounding=self.loan_borrow_disbursement_payment_wizard_id.order_id.company_id.currency_id.rounding) == 1:
                line2['amount_currency'] = abs(amount_currency)

        return [(0, 0, line1), (0, 0, line2)]

    def _prepare_amounts(self):
        ctx = dict(self._context, lang=self.partner_id.lang)
        company_currency = self.loan_borrow_disbursement_payment_wizard_id.order_id.company_id.currency_id
        diff_currency = self.currency_id != company_currency
        if diff_currency:
            amount_currency = self.value
            # amount = self.currency_id.with_context(ctx)._convert(self.value, company_currency, self.loan_borrow_disbursement_payment_wizard_id.order_id.company_id, self.loan_borrow_disbursement_payment_wizard_id.payment_date)
            amount = self.value * self.rate
        else:
            amount_currency = False
            amount = self.value

        if self.payment_type == 'outbound':
            amount = -1 * amount
            amount_currency = -1 * amount_currency

        possitive_amount = float_compare(amount, 0.0, precision_rounding=self.currency_id.rounding) == 1
        return amount, amount_currency, diff_currency, possitive_amount

    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     self.invoice_ids = False
    #     self.purchase_order_ids = False

    # @api.onchange('x_payment_type')
    # def onchange_x_payment_type(self):
    #     if self.x_payment_type == 'deposit':
    #         if len(self.purchase_order_ids) > 1:
    #             self.purchase_order_ids = False
    #         self.invoice_ids = False
    #         self.x_type = 'contract'


    @api.onchange( 'purchase_order_ids','x_payment_type')
    def _onchange_payment_type_po(self):
        if self.x_payment_type == 'deposit':
            if len(self.purchase_order_ids) > 1:
                self.purchase_order_ids = False
            self.invoice_ids = False
            self.x_type = 'contract'
        for item in self:
            if item.x_payment_type == 'deposit' and len(item.purchase_order_ids) >1:
                raise UserError(_("Only 1 deposit per line is allowed."))

    @api.onchange('x_type')
    def onchange_x_type(self):
        if self.x_type == 'contract':
            self.invoice_ids = False
            self.lc_ids = False
        if self.x_type == 'lc':
            self.purchase_order_ids = False
            self.invoice_ids = False
        else:
            self.purchase_order_ids = False
            self.lc_ids = False

    @api.onchange('rate')
    def onchange_rate(self):
        if self.rate and self.rate != 0:
            # self.value_natural_currency = self.value * self.rate
            self.value_natural_currency = float_round(self.value * self.rate, precision_rounding=self.order_id.currency_id.rounding)
        else:
            self.value_natural_currency = self.value

    @api.onchange('value')
    def onchange_value(self):
        if self.value:
            if self.rate and self.rate != 0:
                # self.value_natural_currency = self.value * self.rate
                self.value_natural_currency = float_round(self.value * self.rate, precision_rounding=self.order_id.currency_id.rounding)
            else:
                self.value_natural_currency = self.value

    @api.onchange('currency_id')
    def onchange_currency(self):
        if self.currency_id:
            # self.rate = self.currency_id._get_x_rate(self.order_id.company_id,self.loan_borrow_disbursement_payment_wizard_id.payment_date)
            self.rate = self.currency_id.with_context(date=self.loan_borrow_disbursement_payment_wizard_id.payment_date).x_rate

    @api.onchange('partner_id')
    def onchange_payment(self):
        if self.partner_id:
            # ls_lc = []
            # lc_ids = self.env['stock.landed.cost'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'done')])
            for res_bank_partner in self.partner_id.bank_ids:
                if res_bank_partner:
                    self.beneficiary_bank_id = res_bank_partner.id
                    break
            # for item in lc_ids:
            #     if any( x.invoice_payment_state != 'paid' and x.state == 'posted' for x in item.vendor_bill_ids):
            #         ls_lc.append(item.id)
            return {
                'domain': {
                    'purchase_order_ids': [('partner_id', '=', self.partner_id.id),
                                          ('state', 'not in', ('draft', 'cancel'))],
                    'invoice_ids': [('partner_id', '=', self.partner_id.id), ('state', '=', 'posted'),('move_type', '=', 'in_invoice')],
                    # 'lc_ids': [('partner_id', '=', self.partner_id.id), ('state', '=', 'done'), ('id', 'in', ls_lc)],
                }
            }

    @api.onchange('order_id')
    def onchange_order_id(self):
        if self.order_id.id:
            self.analytic_account_id = self.order_id.analytic_account_id
            self.object_cost_id = self.order_id.object_cost_id
            self.part_id = self.order_id.part_id


    @api.onchange('purchase_order_ids')
    def onchange_purchase_order(self):
        if len(self.purchase_order_ids) > 0:
            self.origin = ', '.join(self.purchase_order_ids.filtered(lambda a: a.origin != False ).mapped('origin'))
            self.currency_id = self.purchase_order_ids[0].currency_id
            if not self.partner_id:
                self.partner_id = self.purchase_order_ids[0].partner_id
            value = 0
            if self.x_payment_type == 'deposit':
                if self.purchase_order_ids[0].payment_term_id:
                    payment_term_line_id = self.env['account.payment.term.line'].search(
                        [('payment_id', '=', self.purchase_order_ids[0].payment_term_id.id),
                         ('value', '=', 'percent')], limit=1)
                    if payment_term_line_id:
                        value = payment_term_line_id.value_amount * self.purchase_order_ids[0].amount_total / 100
            else:

                for purchase_order_id in self.purchase_order_ids:
                    amount = purchase_order_id.amount_total
                    # if purchase_order_id.amount_due > purchase_order_id.invoiced_amount:
                    #     amount = purchase_order_id.invoiced_amount - (purchase_order_id.amount_due-purchase_order_id.invoiced_amount)
                    value += purchase_order_id.currency_id._convert(amount, purchase_order_id.currency_id,
                        purchase_order_id.company_id,
                        purchase_order_id.date_order or fields.Date.today())
            self.value = value
            self.payment_type= 'outbound'



    @api.onchange('lc_ids')
    def onchange_lc_ids(self):
        if len(self.lc_ids)> 0:
            if not self.partner_id:
                self.partner_id = self.lc_ids[0].partner_id
            self.invoice_ids = self.lc_ids.mapped('vendor_bill_ids').filtered(lambda x: x.partner_id == self.partner_id)

    @api.onchange('invoice_ids')
    def onchange_invoice_ids(self):
        if len(self.invoice_ids) > 0:
            self.origin = ', '.join(self.invoice_ids.filtered(lambda a: a.ref != False ).mapped('ref'))
            # if self.x_payment_type == 'deposit':
            #     if self.purchase_order_id.payment_term_id:
            #         payment_term_line_id = self.env['account.payment.term.line'].search(
            #             [('payment_id', '=', self.purchase_order_id.payment_term_id.id),
            #              ('value', '=', 'percent')], limit=1)
            #         if payment_term_line_id:
            #             self.value = payment_term_line_id.value_amount * self.purchase_order_id.amount_total / 100

            if not self.partner_id:
                self.partner_id = self.invoice_ids[0].partner_id
            self.currency_id = self.invoice_ids[0].currency_id
            value = 0
            for invoice_id in self.invoice_ids.filtered(lambda x: x.state in ('open','posted')):
                amount = invoice_id.amount_residual
                if invoice_id.amount_residual > invoice_id.amount_total:
                    amount = invoice_id.amount_total - (invoice_id.amount_residual - invoice_id.amount_total)
                value += invoice_id.currency_id._convert(amount, invoice_id.currency_id,
                    invoice_id.company_id,
                    invoice_id.date or fields.Date.today())
            self.value = value
            self.payment_type= 'outbound'


    def action_show_popup_choose_word_tpl(self):
        self.ensure_one()
        return {
            'name': _('Print Template'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'template.bank.wizard',
            'no_destroy': False,
            'target': 'new',
            'view_id': self.env.ref(
                'to_loan_management.word_template_wizard_form') and self.env.ref(
                'to_loan_management.word_template_wizard_form').id or False,
            'context': {'default_disbursement_detail_id': self.id,
                        'default_borrow_disbursement_id': self.loan_disbursement_id.id},
        }

    @api.model
    def create(self, vals):
        return super(LoanBorrowDisbursementDetailWizard, self).create(vals)
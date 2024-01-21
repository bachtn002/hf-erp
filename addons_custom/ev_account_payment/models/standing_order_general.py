# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_standing_order_id = fields.Many2one('standing.order.general', 'Standing Order')


class StandingOrderGeneral(models.Model):
    _name = 'standing.order.general'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda self: _('New'), readonly=True, copy=False, track_visibility='onchange')
    payment_type = fields.Selection([('deposit', 'Deposit'), ('pay', 'Pay')], default='pay', string='Payment Type',
                                    track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', 'Account Journal', domain=[('type', 'in', ('cash', 'bank'))],
                                 track_visibility='onchange')
    beneficiary = fields.Char('Beneficiary')
    amount_total = fields.Float('Amount', track_visibility='onchange')
    date = fields.Date('Date', default=lambda self: fields.Date.today(), track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  track_visibility='onchange')
    rate = fields.Float('Rate', track_visibility='onchange')
    lines = fields.One2many('standing.order.general.line', 'standing_order_id', 'Details', ondelete='cascade')
    payment_ids = fields.One2many('account.payment', 'x_standing_order_id', 'Payment Lines')
    description = fields.Text('Description', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')],
        default='draft', copy=False, string="Status", track_visibility='onchange')

    default_credit_account_id = fields.Many2one('account.account', related='journal_id.default_account_id',
                                                string='Credit Account')

    @api.onchange('lines', 'lines.value')
    def _onchange_amount_total(self):
        self.amount_total = sum(self.lines.mapped('value'))
        # if amount_total != self.amount_total:
        #     raise UserError(_("Amount total differance sum lines!"))

    def unlink(self):
        if self.state != 'draft':
            raise UserError(_("You cannot delete record if the state is not 'Draft'."))
        return super(StandingOrderGeneral, self).unlink()

    @api.onchange('currency_id')
    def onchange_currency(self):
        if self.currency_id:
            self.rate = self.currency_id.x_rate

    @api.onchange('rate')
    def onchange_rate(self):
        for item in self.lines:
            item.value_natural_currency = self.rate * item.value

    def action_confirm(self):
        name = self.env['account.journal'].browse(self.journal_id.id).sequence_id.next_by_id()
        self.write({'name': name})
        AccountPayment = self.env['account.payment']
        AccountPaymentLine = self.env['account.payment.line']
        for line in self.lines:
            payment_id = AccountPayment.with_context(
                {'default_payment_type': 'outbound', 'default_partner_type': 'supplier', 'default_bank': 'bank',
                 'default_x_is_payment_vendor_bank': True, 'default_payment_method_id': 2}).create({
                'x_partner_id': line.partner_id.id,
                'x_payment_type': self.payment_type,
                'x_partner_bank_id': line.partner_bank_id.id,
                'tax_code': line.tax_code,
                'x_receiver': line.receiver,
                'x_address': line.address,
                'x_description': self.description if self.description else line.name,
                'x_allocation_type': line.allocation_type,
                'x_journal_id': self.journal_id.id,
                'date': self.date,
                'x_date': self.date,
                'currency_id': self.currency_id.id,
                'x_rate': self.rate,
                'company_id': self.company_id.id,
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'bank': 'bank',
                'x_is_payment_vendor_bank': True,
                'payment_method_id': 2,
                'x_standing_order_id': self.id,
            })
            payment_line_id = AccountPaymentLine.create({
                'payment_id': payment_id.id,
                'purchase_order_id': line.purchase_order_id.id,
                'origin': line.origin,
                'name': line.name,
                'destination_account_id': line.destination_account_id.id,
                'account_id': line.account_id.id,
                'value': line.value,
                'value_natural_currency': line.value_natural_currency,
                'currency_id': self.currency_id.id,
                'rate': self.rate,
                'analytic_account_id': line.analytic_account_id.id,
            })
            payment_id.action_confirm()
        if all([x.state == 'reconciled' for x in self.payment_ids]):
            self.state = 'reconciled'
        else:
            self.state = 'posted'

    def action_print(self):
        pass

    def action_draft(self):
        for line in self.payment_ids:
            line.action_draft()
        if all([x.state == 'draft' for x in self.payment_ids]):
            self.state = 'draft'
            for line in self.payment_ids:
                line.unlink()
        else:
            raise UserError(_("You cannot back a payment that is already posted."))

    def action_back(self):
        for line in self.payment_ids:
            line.action_back()
        if all([x.state == 'draft' for x in self.payment_ids]):
            self.state = 'draft'
            for line in self.payment_ids:
                line.unlink()
        else:
            raise UserError(_("You cannot back a payment that is already posted."))

    def action_show_popup_print_unc(self):
        self.ensure_one()
        return {
            'name': _('Print UNC'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'standing.order.general.unc',
            'no_destroy': False,
            'target': 'new',
            'view_id': self.env.ref(
                'ev_account_payment.wizard_standing_order_general_unc_view_form') and self.env.ref(
                'ev_account_payment.wizard_standing_order_general_unc_view_form').id or False,
            'context': {'default_general_id': self.id},
        }


class StandingOrderGeneralLine(models.Model):
    _name = 'standing.order.general.line'

    standing_order_id = fields.Many2one('standing.order.general', 'Standing Order')
    name = fields.Char('Description')
    value = fields.Float('Value', required=True)
    value_natural_currency = fields.Float('Value natural currency')
    account_id = fields.Many2one('account.account', 'Account credit')
    destination_account_id = fields.Many2one('account.account', 'Destination account')
    partner_id = fields.Many2one('res.partner', 'Partner')
    receiver = fields.Char('Receiver')
    address = fields.Char('Address')
    partner_bank_id = fields.Many2one('res.partner.bank', 'Partner bank', domain="[('partner_id', '=', partner_id)]")
    tax_code = fields.Char('Tax Code')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    origin = fields.Char('Origin')
    allocation_type = fields.Selection([('auto', 'Automatic'), ('manual', 'Manual')], default='auto',
                                       string='Allocation Type')

    @api.onchange('value')
    def onchange_value(self):
        if self.value:
            if self.standing_order_id.rate and self.standing_order_id.rate != 0:
                self.value_natural_currency = self.value * self.standing_order_id.rate
            else:
                self.value_natural_currency = self.value

    @api.onchange('purchase_order_id')
    def onchange_purchase_order(self):
        if self.purchase_order_id:
            self.origin = self.purchase_order_id.origin
            self.partner_id = self.purchase_order_id.partner_id.id
            if self.standing_order_id.payment_type == 'deposit':
                if self.purchase_order_id.payment_term_id:
                    payment_term_line_id = self.env['account.payment.term.line'].search(
                        [('payment_id', '=', self.purchase_order_id.payment_term_id.id),
                         ('value', '=', 'percent')], limit=1)
                    if payment_term_line_id:
                        self.value = payment_term_line_id.value_amount * self.purchase_order_id.amount_total / 100
                if self.purchase_order_id.company_id.x_account_deposit_id:
                    self.destination_account_id = self.purchase_order_id.company_id.x_account_deposit_id
                else:
                    raise UserError(_("You have not configured a deposit account."))

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            partner_bank = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)], order='id',
                                                               limit=1)
            if partner_bank:
                self.partner_bank_id = partner_bank
            else:
                self.partner_bank_id = False
            self.tax_code = self.partner_id.vat
            self.receiver = self.partner_id.x_legal_representation
            self.address = self.partner_id.street
            ids = []
            for id in self.partner_id.bank_ids:
                ids.append(id.id)
            return {
                'domain': {
                    'partner_bank_id': [('id', 'in', ids)]
                }
            }

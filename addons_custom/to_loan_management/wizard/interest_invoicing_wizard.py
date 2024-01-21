from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AbstractInterestInvoicingWizard(models.AbstractModel):
    _name = 'abstract.interest.invoicing.wizard'
    _description = "Share business logics between Interest Invoicing Wizard"

    @api.model
    def _get_interest_lines(self):
        model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])
        return self.env[model].browse(active_ids)

    def _get_invoice_type(self):
        raise ValidationError(_("The method `_get_invoice_type()` has not been implemented for the model %s") % (self._name,))

    def _get_partner_account(self, partner_id):
        raise ValidationError(_("The method `_get_partner_account(partner_id)` has not been implemented for the model %s") % (self._name,))

    def _prepare_invoice(self, **kwarg):
        partner = kwarg.get('partner_id', False)
        if not partner:
            raise ValidationError(_("No partner passed for invoicing interests"))
        company = kwarg.get('company_id', False)
        if not company:
            raise ValidationError(_("No company passed for invoicing interests"))
        account_id = self._get_partner_account(partner)
        currency_id = kwarg.get('currency_id', False)
        loan_disbursement_id = kwarg.get('loan_disbursement_id', False)
        if not currency_id:
            raise ValidationError(_("No currency passed for invoicing interests"))
        fiscal_position_id = kwarg.get('fiscal_position_id', partner.property_account_position_id)
        user_id = kwarg.get('user_id', False)
        origin = kwarg.get('origin', '')

        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """

        journal_id = kwarg.get('journal_id', self.env['account.move'].default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_('No Journal found for interests invoicing.'))
        invoice_vals = {
            'invoice_origin': origin,
            'move_type': self._get_invoice_type(),
            'partner_id': partner.id,
#             'partner_shipping_id': partner.id, # v12-13, field này chỉ có ở module sale, module này k depends vào sale
            'journal_id': journal_id.id,
            'currency_id': currency_id.id,
            'loan_disbursement_id': loan_disbursement_id,
#             'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': fiscal_position_id.id,
            'company_id': company.id,
            'user_id': user_id and user_id.id or False,
            'invoice_line_ids': kwarg.get('invoice_line_ids', False)
        }
        return invoice_vals

    def _get_invoice_action_xml_id(self):
        raise ValidationError(_("The method `_get_invoice_action_xml_id()` has not been implemented for the model '%s'") % (self._name,))

    def _get_invoice_form_view_xml_id(self):
        return 'account.view_move_form'

    def create_invoices(self):
        invoice_ids = self.env['account.move']
        self.ensure_one()
        if not self.interest_line_ids:
            raise ValidationError(_("No interest line to invoice"))
        for line in self.interest_line_ids:
            if line.state != 'confirmed':
                raise ValidationError(_("You may not be able to invoice the interest line '%s' which is not in Confirmed state.\n"
                                        "Tips: massively confirmation action is available at Interest list views...") % (line.name,))
            if line.fully_invoiced:
                raise ValidationError(_("The interest '%s' of the contract '%s' has been fully invoiced.") % (line.name, line.order_id.name))

        company_ids = self.interest_line_ids.mapped('order_id.company_id')
        for company in company_ids:
            company_interest_line_ids = self.interest_line_ids.filtered(lambda l: l.order_id.company_id.id == company.id)
            for currency in company_interest_line_ids.mapped('order_id.currency_id'):
                currency_interest_line_ids = company_interest_line_ids.filtered(lambda l: l.currency_id.id == currency.id)
                for partner in currency_interest_line_ids.mapped('order_id.partner_id'):
                    partner_interest_line_ids = currency_interest_line_ids.filtered(lambda l: l.order_id.partner_id.id == partner.id)
                    for journal in partner_interest_line_ids.mapped('order_id.journal_id'):
                        invoice_line_ids = []
                        line_ids = currency_interest_line_ids.filtered(lambda l: l.order_id.journal_id.id == journal.id)
                        for line in line_ids:
                            data = line._prepare_inv_line_data()
                            invoice_line_ids.append((0, 0, data))

                        user_ids = line_ids.mapped('order_id.user_id')
                        invoice_data = self._prepare_invoice(
                            company_id=company,
                            partner_id=partner,
                            currency_id=currency,
                            journal_id=journal,
                            origin=', '.join(line_ids.mapped('order_id.name')),
                            user_id=user_ids and user_ids[0] or False,
                            loan_disbursement_id=line.disbursement_id.id,
                            invoice_line_ids=invoice_line_ids
                            )
                        new_inv = invoice_ids.create(invoice_data)
                        invoice_ids += new_inv

        if self.env.context.get('view_invoices', False) and invoice_ids:
            action = self.env.ref(self._get_invoice_action_xml_id()).read()[0]
            if len(invoice_ids) > 1:
                action['domain'] = [('id', 'in', invoice_ids.ids)]
            elif len(invoice_ids) == 1:
                res = self.env.ref(self._get_invoice_form_view_xml_id(), False)
                action['views'] = [(res and res.id or False, 'form')]
                action['res_id'] = invoice_ids.ids[0]
            return action


class BorrowInterestInvoicingWizard(models.TransientModel):
    _name = "borrow.interest.invoicing.wizard"
    _inherit = 'abstract.interest.invoicing.wizard'
    _description = "Borrowing Loan Interest Invoicing Wizard"

    interest_line_ids = fields.Many2many('loan.borrow.interest.line', string='Interests to Invoice',
                                         default=lambda self: self._get_interest_lines())

    def _get_invoice_type(self):
        return 'in_invoice'

    def _get_invoice_action_xml_id(self):
        return 'account.action_move_in_invoice_type'

    def _get_partner_account(self, partner_id):
        return partner_id.property_account_payable_id


class LendInterestInvoicingWizard(models.TransientModel):
    _name = "lend.interest.invoicing.wizard"
    _inherit = 'abstract.interest.invoicing.wizard'
    _description = "Lending Loan Interest Invoicing Wizard"

    interest_line_ids = fields.Many2many('loan.lend.interest.line', string='Interests to Invoice',
                                         default=lambda self: self._get_interest_lines())

    def _get_invoice_type(self):
        return 'out_invoice'

    def _get_invoice_action_xml_id(self):
        return 'account.action_move_out_invoice_type'

    def _get_partner_account(self, partner_id):
        return partner_id.property_account_receivable_id

    def create_invoices(self):
        active_model = self.env.context.get('active_model', False)
        interest_line_ids = self._context.get('active_ids', [])
        if active_model == 'loan.borrow.interest.line':
            interest_line_ids = self.env['loan.borrow.interest.line'].browse(interest_line_ids)
        # elif active_model == 'loan.lend.interest.line':
        #     interest_line_ids = self.env['loan.lend.interest.line'].browse(interest_line_ids)
        # elif active_model == 'loan.lend.interest.line':
        #     interest_line_ids = self.env['loan.lend.interest.line'].browse(interest_line_ids)


        line_objs = self.env[active_model].browse(interest_payment_line_ids)
        if not interest_payment_line_ids:
            return {'type': 'ir.actions.act_window_close'}
        if line_objs[0].order_id:
            obj = self.env['loan.borrowing.order'].browse(line_objs[0].order_id.id)
        # elif line_objs[0].lending_order_id:
        #     obj = self.env['loan.lending.order'].browse(line_objs[0].lending_order_id.id)
        # res = obj[0].manual_invoice(interest_payment_line_ids)
        if self._context.get('view_invoices', False):
            return res
        return {'type': 'ir.actions.act_window_close'}


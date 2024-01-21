from odoo import models, fields, api, _


class AccountPaymentUncWizard(models.TransientModel):
    _name = 'account.payment.unc.wizard'
    _description = 'Print UNC'
    _rec_name = 'payment_id'

    payment_id = fields.Many2one('account.payment', 'Account Payment')
    x_bank_id = fields.Many2one('res.bank', 'Bank')
    x_account_number = fields.Char(string='Account Number')

    def action_print_unc_vendor(self):
        if self.x_bank_id.bic == 'VCB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.template_vcb_unc_vendor/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'BIDV':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.template_bidv_unc_vendor/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.x_bank_id.bic == 'VTB':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/ev_account_payment.template_vtb_unc_vendor/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }

    @api.onchange('x_bank_id')
    def _onchange_x_bank_id(self):
        if self.payment_id:
            res_partner_bank = self.env['res.partner'].search([('id', '=', self.payment_id.company_id.partner_id.id)], limit=1)
            acc_number = 0
            if res_partner_bank.bank_ids:
                for item in res_partner_bank.bank_ids:
                    if item.bank_id == self.x_bank_id:
                        acc_number = item.acc_number
                        break
            if acc_number:
                self.x_account_number = acc_number
            else:
                self.x_account_number = ' '

    def _get_name_bank(self):
        name = ''
        if self.payment_id.x_partner_bank_id.bank_id:
            name = str(self.payment_id.x_partner_bank_id.bank_id.name)
            name += " " + str(self.payment_id.x_partner_bank_id.bank_id.street) if self.payment_id.x_partner_bank_id.bank_id.street else ''
        return name

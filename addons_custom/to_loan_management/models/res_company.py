import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class res_company(models.Model):
    _inherit = "res.company"

    loan_borrowing_journal_id = fields.Many2one('account.journal', string='Borrowing Journal')
    loan_borrowing_account_id = fields.Many2one('account.account', string='Loan Borrowing Account')
    loan_lending_journal_id = fields.Many2one('account.journal', string='Lending Journal')
    loan_lending_account_id = fields.Many2one('account.account', string='Loan Lending Account')

    def _prepare_borrowing_loan_journal_data(self):
        return {
            'name': _('Borrowing Loans Journal'),
            'type': 'purchase',
            'code': 'BLJ',
            'show_on_dashboard': True,
            'sequence': 12,
            'company_id':self.id,
            }
        
    def _prepare_lending_loan_journal_data(self):
        return {
            'name': _('Lending Loans Journal'),
            'type': 'sale',
            'code': 'LLJ',
            'show_on_dashboard': True,
            'sequence': 13,
            'company_id':self.id,
            }

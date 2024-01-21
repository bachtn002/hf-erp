from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    module_to_loan_management = fields.Boolean("Loan Management")
    loan_borrowing_journal_id = fields.Many2one('account.journal', string='Borrowing Journal',
                                                related='company_id.loan_borrowing_journal_id',readonly=False)
    loan_borrowing_account_id = fields.Many2one('account.account', string='Loan Borrowing Account',
                                                related='company_id.loan_borrowing_account_id',readonly=False)
    loan_lending_journal_id = fields.Many2one('account.journal', string='Lending Journal',
                                              related='company_id.loan_lending_journal_id',readonly=False)
    loan_lending_account_id = fields.Many2one('account.account', string='Loan Lending Account',
                                              related='company_id.loan_lending_account_id',readonly=False)
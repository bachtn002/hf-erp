from odoo import api, models, fields, _


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    property_borrowing_account_id = fields.Many2one('account.account.template', string='Borrowing Loan Account')
    property_lending_account_id = fields.Many2one('account.account.template', string='Lending Loan Account')

    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        journal_data = super(AccountChartTemplate, self)._prepare_all_journals(acc_template_ref=acc_template_ref, company=company, journals_dict=journals_dict)
        borrowing_loan_journal_data = company._prepare_borrowing_loan_journal_data()
        borrowing_loan_journal_data.update({
            'default_debit_account_id': acc_template_ref.get(self.property_borrowing_account_id.id),
            'default_credit_account_id': acc_template_ref.get(self.property_borrowing_account_id.id),
            })
        journal_data.append(borrowing_loan_journal_data)

        lending_loan_journal_data = company._prepare_lending_loan_journal_data()
        lending_loan_journal_data.update({
            'default_debit_account_id': acc_template_ref.get(self.property_lending_account_id.id),
            'default_credit_account_id': acc_template_ref.get(self.property_lending_account_id.id),
            })
        journal_data.append(lending_loan_journal_data)
        return journal_data

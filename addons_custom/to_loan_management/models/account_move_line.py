from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    loan_borrow_interest_line_id = fields.Many2one('loan.borrow.interest.line', string='Loan Borrow Interest Line')
    loan_lend_interest_line_id = fields.Many2one('loan.lend.interest.line', string='Loan Lend Interest Line')

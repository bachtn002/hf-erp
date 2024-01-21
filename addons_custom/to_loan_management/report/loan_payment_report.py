from odoo import models, fields, api
from odoo import tools


class LoanPaymentReport(models.Model):
    _name = "loan.payment.report"
    _description = "Loan Payment Analysis"
    _auto = False

    date = fields.Date('Date', readonly=True)
    user_id = fields.Many2one('res.users', 'User', readonly=True)
    name = fields.Char('Description', size=64, readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    company_id = fields.Many2one('res.company', 'Company', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    account_id = fields.Many2one('account.analytic.account', 'Account', required=False)
    general_account_id = fields.Many2one('account.account', 'General Account', required=True)
    move_id = fields.Many2one('account.move.line', 'Move', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True)
    amount = fields.Float('Amount', readonly=True)
    unit_amount = fields.Integer('Unit Amount', readonly=True)
    nbr_entries = fields.Integer('# Entries', readonly=True)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
            SELECT
                 
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _sub_select_disbursement_payment_match(self):
        return """
            SELECT
                dpm.matched_amount                
        """

    def _from_disbursement_payment_match(self):
        return """
            FROM loan_borrow_disbursement_payment_match AS dpm
                JOIN loan_disbursement_payment
        """

    def _from(self):
        from_str = """
            FROM
                account_analytic_line a, account_analytic_account analytic
        """
        return from_str

    def _join(self):
        join_str = """
        """
        return join_str

    def _where(self):
        where_str = """
            WHERE analytic.id = a.account_id
        """
        return where_str

    def _group_by(self):
        group_by_str = """
        GROUP BY
            a.date, a.user_id,a.name,analytic.partner_id,a.company_id,a.currency_id,
            a.account_id,a.general_account_id,
            a.move_id,a.product_id,a.product_uom_id
        """
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
                 %s
                 %s
                 %s
                 %s
                 %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by()))

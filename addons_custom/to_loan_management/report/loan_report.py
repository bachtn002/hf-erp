from odoo import models, fields, api
from odoo import tools


class LoanReport(models.Model):
    _name = "loan.report"
    _description = "Loan Analysis"
    _auto = False

    name = fields.Char(string='Ref.', readonly=True)
    order_name = fields.Char(string='Contract', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')], string='Status', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    date_confirmed = fields.Date(string='Date Confirmed', readonly=True)
    date_maturity = fields.Date(string='Due Date', readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    type = fields.Selection([
        ('disbursement', 'Disbursement'),
        ('refund', 'Principal Refund'),
        ('interest', 'Interest')], string='Transaction Type', readonly=True)
    loan_type = fields.Selection([
        ('borrow', 'Borrowing')], string='Loan Type', readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s AS (
                WITH currency_rate as (%s)
                SELECT
                    l.id,
                    l.name,
                    o.name AS order_name,
                    l.date,
                    l.date_maturity,
                    l.date_confirmed,
                    SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
                    l.partner_id,
                    l.state,
                    o.company_id AS company_id,
                    'borrow' AS loan_type,
                    'disbursement' AS type
                    
                FROM
                    loan_borrow_disbursement AS l
                    JOIN loan_borrowing_order AS o ON o.id = l.order_id
                    LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
                        cr.company_id = l.company_id and
                        cr.date_start <= coalesce(l.date_confirmed, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(l.date_confirmed, now())))
                GROUP BY
                    l.id,
                    o.name,
                    l.date,
                    l.date_maturity,
                    l.date_confirmed,
                    l.partner_id,
                    l.state,
                    o.company_id,
                    cr.rate
                    
                UNION ALL
                SELECT
                    l.id,
                    l.name,
                    o.name AS order_name,
                    l.date,
                    l.date_maturity,
                    l.date_confirmed,
                    -1.0 * SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
                    l.partner_id,
                    l.state,
                    o.company_id AS company_id,
                    'borrow' AS loan_type,
                    'refund' AS type
                FROM
                    loan_borrow_refund_line AS l
                    JOIN loan_borrowing_order AS o ON o.id = l.order_id
                    LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
                        cr.company_id = l.company_id and
                        cr.date_start <= coalesce(l.date_confirmed, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(l.date_confirmed, now())))
                GROUP BY
                    l.id,
                    o.name,
                    l.date,
                    l.date_maturity,
                    l.date_confirmed,
                    l.partner_id,
                    l.state,
                    o.company_id,
                    cr.rate
                    
                UNION ALL
                SELECT
                    l.id,
                    l.name,
                    o.name AS order_name,
                    l.date_to AS date,
                    l.date_maturity,
                    l.date_confirmed,
                    -1.0 * SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
                    o.partner_id,
                    l.state,
                    o.company_id AS company_id,
                    'borrow' AS loan_type,
                    'interest' AS type
                FROM
                    loan_borrow_interest_line AS l
                    JOIN loan_borrowing_order AS o ON o.id = l.order_id
                    LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
                        cr.company_id = l.company_id and
                        cr.date_start <= coalesce(l.date_to, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(l.date_to, now())))
                GROUP BY
                    l.id,
                    o.name,
                    l.date_to,
                    l.date_maturity,
                    l.date_confirmed,
                    o.partner_id,
                    l.state,
                    o.company_id,
                    cr.rate
            )
        """ % (self._table, self.env['res.currency']._select_companies_rates())
        )

# sql báo cáo vay/cho vay
# """
#             CREATE or REPLACE VIEW %s AS (
#                 WITH currency_rate as (%s)
#                 SELECT
#                     l.id,
#                     l.name,
#                     o.name AS order_name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
#                     l.partner_id,
#                     l.state,
#                     o.company_id AS company_id,
#                     'borrow' AS loan_type,
#                     'disbursement' AS type
#
#                 FROM
#                     loan_borrow_disbursement AS l
#                     JOIN loan_borrowing_order AS o ON o.id = l.order_id
#                     LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
#                         cr.company_id = l.company_id and
#                         cr.date_start <= coalesce(l.date_confirmed, now()) and
#                         (cr.date_end is null or cr.date_end > coalesce(l.date_confirmed, now())))
#                 GROUP BY
#                     l.id,
#                     o.name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     l.partner_id,
#                     l.state,
#                     o.company_id,
#                     cr.rate
#
#                 UNION ALL
#                 SELECT
#                     l.id,
#                     l.name,
#                     o.name AS order_name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     -1.0 * SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
#                     l.partner_id,
#                     l.state,
#                     o.company_id AS company_id,
#                     'lend' AS loan_type,
#                     'disbursement' AS type
#                 FROM
#                     loan_lend_disbursement AS l
#                     JOIN loan_lending_order AS o ON o.id = l.order_id
#                     LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
#                         cr.company_id = l.company_id and
#                         cr.date_start <= coalesce(l.date_confirmed, now()) and
#                         (cr.date_end is null or cr.date_end > coalesce(l.date_confirmed, now())))
#                 GROUP BY
#                     l.id,
#                     o.name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     l.partner_id,
#                     l.state,
#                     o.company_id,
#                     cr.rate
#
#                 UNION ALL
#                 SELECT
#                     l.id,
#                     l.name,
#                     o.name AS order_name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     -1.0 * SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
#                     l.partner_id,
#                     l.state,
#                     o.company_id AS company_id,
#                     'borrow' AS loan_type,
#                     'refund' AS type
#                 FROM
#                     loan_borrow_refund_line AS l
#                     JOIN loan_borrowing_order AS o ON o.id = l.order_id
#                     LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
#                         cr.company_id = l.company_id and
#                         cr.date_start <= coalesce(l.date_confirmed, now()) and
#                         (cr.date_end is null or cr.date_end > coalesce(l.date_confirmed, now())))
#                 GROUP BY
#                     l.id,
#                     o.name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     l.partner_id,
#                     l.state,
#                     o.company_id,
#                     cr.rate
#
#                 UNION ALL
#                 SELECT
#                     l.id,
#                     l.name,
#                     o.name AS order_name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
#                     l.partner_id,
#                     l.state,
#                     o.company_id as company_id,
#                     'lend' AS loan_type,
#                     'refund' AS type
#                 FROM
#                     loan_lend_refund_line AS l
#                     JOIN loan_lending_order AS o ON o.id = l.order_id
#                     LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
#                         cr.company_id = l.company_id and
#                         cr.date_start <= coalesce(l.date_confirmed, now()) and
#                         (cr.date_end is null or cr.date_end > coalesce(l.date_confirmed, now())))
#                 GROUP BY
#                     l.id,
#                     o.name,
#                     l.date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     l.partner_id,
#                     l.state,
#                     o.company_id,
#                     cr.rate
#
#                 UNION ALL
#                 SELECT
#                     l.id,
#                     l.name,
#                     o.name AS order_name,
#                     l.date_to AS date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     -1.0 * SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
#                     o.partner_id,
#                     l.state,
#                     o.company_id AS company_id,
#                     'borrow' AS loan_type,
#                     'interest' AS type
#                 FROM
#                     loan_borrow_interest_line AS l
#                     JOIN loan_borrowing_order AS o ON o.id = l.order_id
#                     LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
#                         cr.company_id = l.company_id and
#                         cr.date_start <= coalesce(l.date_to, now()) and
#                         (cr.date_end is null or cr.date_end > coalesce(l.date_to, now())))
#                 GROUP BY
#                     l.id,
#                     o.name,
#                     l.date_to,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     o.partner_id,
#                     l.state,
#                     o.company_id,
#                     cr.rate
#
#                 UNION ALL
#                 SELECT
#                     l.id,
#                     l.name,
#                     o.name AS order_name,
#                     l.date_to AS date,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     SUM(l.amount) / COALESCE(cr.rate, 1.0) AS amount,
#                     o.partner_id,
#                     l.state,
#                     o.company_id as company_id,
#                     'lend' AS loan_type,
#                     'interest' AS type
#                 FROM
#                     loan_lend_interest_line AS l
#                     JOIN loan_lending_order AS o ON o.id = l.order_id
#                     LEFT JOIN currency_rate cr on (cr.currency_id = l.currency_id and
#                         cr.company_id = l.company_id and
#                         cr.date_start <= coalesce(l.date_to, now()) and
#                         (cr.date_end is null or cr.date_end > coalesce(l.date_to, now())))
#                 GROUP BY
#                     l.id,
#                     o.name,
#                     l.date_to,
#                     l.date_maturity,
#                     l.date_confirmed,
#                     o.partner_id,
#                     l.state,
#                     o.company_id,
#                     cr.rate
#             )
#         """
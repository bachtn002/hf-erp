from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # recompute fully_invoiced of all interest lines. They were all wrong
    env['loan.borrow.interest.line'].search([])._compute_fully_invoiced()
    env['loan.lend.interest.line'].search([])._compute_fully_invoiced()
    # serach all existing refund payments and reconcile their reconcialble lines with their corresponding disbursements' lines
    env['loan.refund.payment'].search([]).reconcile_disbusement()


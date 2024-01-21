from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # recompute invoiced_amount of all interest lines. They were all wrong when working with taxes included in price
    env['loan.borrow.interest.line'].search([])._compute_invoiced_amount()
    env['loan.lend.interest.line'].search([])._compute_invoiced_amount()


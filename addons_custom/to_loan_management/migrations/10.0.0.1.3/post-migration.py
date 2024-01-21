from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # serach all existing refund payments and reconcile their reconcialble lines with their corresponding disbursements' lines
    env['loan.refund.payment'].search([]).reconcile_disbusement()


from odoo import api, models, fields, exceptions
import odoo.tools.config as config


class RPTPurchaseOrder(models.TransientModel):
    _name = 'rpt.purchase.order'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')

    def action_export_report(self):
        return


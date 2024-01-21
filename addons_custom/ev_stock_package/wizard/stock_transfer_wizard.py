# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrDepartureWizard(models.TransientModel):
    _name = 'stock.transfer.wizard'
    _description = 'Stock transfer Wizard'

    stock_transfer_id = fields.Many2one('stock.transfer', string='Stock transfer name', readonly=1)

    def action_create_package(self):
        package_id = self.stock_transfer_id.create_new_package()
        if not package_id:
            raise UserError(_("There is no line to create new Pack!"))
        return package_id.action_process()
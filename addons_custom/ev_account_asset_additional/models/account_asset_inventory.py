
from odoo import models, fields, api, _

class AccountAssetInventory(models.Model):
    _inherit = 'account.asset.inventory'

    additional_lines = fields.One2many('account.asset.inventory.add.line','inventory_add_line_id','Additional line')
    # lines = fields.One2many('account.asset.inventory.line', 'inventory_id','Assets',track_visibility='onchange')

    def action_print_excel(self):
        return {
                'type': 'ir.actions.act_url',
                'url': ('/report/xlsx/ev_account_asset_additional.report_asset_inventory/%s' % self.id),
                'target': 'new',
                'res_id': self.id,
                }

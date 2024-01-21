from odoo import models, fields, api

class AccountAssetInventoryAddLine(models.Model):
    _name = 'account.asset.inventory.add.line'
    _description = 'Account Asset Inventory Additonal Line'

    # Tài sản, đơn vị tính, số lượng, Ghi chú
    name = fields.Char("Asset Inventory")
    code = fields.Char("Asset Code")
    unit = fields.Char("Unit")
    quantity = fields.Integer("Quantity")
    note = fields.Char("Note")
    inventory_add_line_id = fields.Many2one('account.asset.inventory','Inventory')

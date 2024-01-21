from odoo import fields, models, api, _

from odoo.exceptions import UserError, _logger


class ProductProduct(models.Model):
    _inherit = 'product.template'

    x_inventory_group_id = fields.Many2one('stock.inventory.group', string="Inventory Group")


class InventoryGroup(models.Model):
    _name = 'stock.inventory.group'

    name = fields.Char(string="Group Name", required=True)
    product_ids = fields.One2many('product.template', 'x_inventory_group_id', string="Products")
    stock_inventory_id = fields.Many2one('stock.inventory', string="Stock Inventory")

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Group Name must be unique'),
    ]

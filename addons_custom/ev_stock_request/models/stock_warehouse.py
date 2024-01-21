from odoo import fields, models, api


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    x_is_supply_warehouse = fields.Boolean('Is Supply Warehouse', default=False)
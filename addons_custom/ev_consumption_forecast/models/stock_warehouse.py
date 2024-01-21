from odoo import models, fields, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    consumption_forecast = fields.Boolean("Consumption Forecast")

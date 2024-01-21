from odoo import models, fields, api


class StockPackageReportLine(models.TransientModel):
    _name = 'stock.package.report.line'

    product_id = fields.Many2one('product.product', string="Product ID")
    qty = fields.Float(string="Quantity", digits='Product Unit of Measure')
    qty_done = fields.Float(string="Quantity Done", digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string="Uom ID")
    package_report_id = fields.Many2one('stock.package.report', string="Package Report ID")


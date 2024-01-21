from odoo import fields, models, api, _
from datetime import datetime

from odoo.exceptions import UserError, _logger
from dateutil.relativedelta import relativedelta


class AllotmentRequestLine(models.Model):
    _name = 'allotment.request.line'
    _description = 'Allotment Request Line'

    allotment_request_id = fields.Many2one('allotment.request', string='Allotment Request')
    product_id = fields.Many2one('product.product', string='Product', change_default=True)
    product_uom = fields.Many2one('uom.uom', string='Uom', related='product_id.uom_id')
    warehoue_des_id = fields.Many2one('stock.warehouse', string='Destination Stock')
    qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
    qty_apply = fields.Float(string='Apply quantity', digits='Product Unit of Measure', default=0)
    stock_transfer_id = fields.Many2one('stock.transfer', string='Stock transfer name', readonly=1)
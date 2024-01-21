import imp
from operator import mod
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductOtherConfigLine(models.Model):
    _name = 'product.other.config.line'
    _description = 'Product Other Config Line'

    # product_id = fields.Many2one(comodel_name='product.product', string="Product ID")
    price_unit_before = fields.Float(string="Price Before", default=0)
    price_unit = fields.Float(string="Price Unit", default=0)
    uom_id = fields.Many2one(comodel_name='uom.uom', string="Uom ID")
    packed_date = fields.Date(string="Packed Date")
    expire_date = fields.Date(string="Expire Date")
    note = fields.Text('Note')
    allow_printing = fields.Boolean('Allow Printing', default=False)
    name_above = fields.Char(string="Name above",  size = 34)
    name_below = fields.Char(string="Name below",  size = 34)
    other_config_id = fields.Many2one(comodel_name='product.other.config', string="Other Config ID")

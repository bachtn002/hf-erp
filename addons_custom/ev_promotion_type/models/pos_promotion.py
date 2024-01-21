from statistics import mode

from attr import fields_dict
from odoo import models, fields, api

class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    promotion_type_id = fields.Many2one('promotion.type','Promotion Type ID')
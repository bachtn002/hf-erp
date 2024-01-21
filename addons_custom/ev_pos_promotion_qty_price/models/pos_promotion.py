# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    type = fields.Selection(selection_add=[
        ('qty_price', 'Quantity Price')
    ])
    pos_promotion_qty_price_ids = fields.One2many('pos.promotion.qty.price', 'promotion_id',
                                                  string="Promotion Quantity Price")

    def download_template_promotion_qty_price(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/ev_pos_promotion_qty_price/static/template/import_gia_ban_theo_so_luong_mua.xls',
            "target": "_parent",
        }

    # @api.constrains('pos_promotion_qty_price_ids')
    # def check_uom_line_pos_promotion_qty_price_ids(self):
    #     for line in self.pos_promotion_qty_price_ids:
    #         if line.qty <= 0:
    #             pass
    #             # raise ValidationError(_("The number of product must be greater than 0!!"))
    #         else:
    #             uom_qty = float_round(line.qty, precision_rounding=line.uom_id.rounding, rounding_method='HALF-UP')
    #             precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #             qty = float_round(line.qty, precision_digits=precision_digits, rounding_method='HALF-UP')
    #             if float_compare(uom_qty, qty, precision_digits=precision_digits) != 0:
    #                 raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
    #                                                               defined on the unit of measure "%s". Please change the quantity done or the \
    #                                                               rounding precision of your unit of measure.') % (
    #                     line.product_id.display_name, line.uom_id.name))

    @api.onchange('type')
    def _onchange_type(self):
        res = super(PosPromotion, self)._onchange_type()
        if self.type != 'qty_price':
            self.pos_promotion_qty_price_ids = False
        return res

from odoo import api, fields, models


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    # Bổ sung thêm 2 loại code: Code khuyến mại, Code khác
    x_promotion_code_type = fields.Selection(string="Promotion code type",
                                             selection=[('code_promo', 'Promotion code'), ('other', 'Other')])
    x_allow_apply_with_other = fields.Boolean("Allow apply with other")


from odoo import fields, models, _


class InheritPosPromotion(models.Model):
    _inherit = 'pos.promotion'
    check_promotion = fields.Boolean(string=_('Promotion Code'))
    x_promotion_condition_or = fields.Boolean(string='Điều kiện hoặc', default=False)
    x_promotion_apply_or = fields.Boolean(string='Áp dụng hoặc', default=False)
    x_accumulate = fields.Boolean(string=_('Accumulate'), default=False)

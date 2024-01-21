from odoo import models, fields, api, _


class LoyaltyRuleCustom(models.Model):
    _inherit = 'loyalty.rule'
    product_rule_rule = fields.Many2many('product.product', 'loyalty_rule_rel', string='Sản phẩm')
    product_cate_rule_rule = fields.Many2many('product.category', string='Nhóm sản phẩm')
    category_id = fields.Many2many('pos.category', string='Loại sản phẩm trên POS')
    valid_product_ids_test = fields.One2many('product.product', compute='_compute_valid_product_ids_test')
    point_per_product = fields.Integer(string='Số điểm trên 1 sản phẩm')
    condition_or = fields.Selection([
        ('product', _('Product')),
        ('product_category', _('Product Category'))],
        string=_('Rule loyalty'),
        default='product',
        required=True,
        tracking=True,
        copy=False)

    @api.depends('product_rule_rule')
    def _compute_valid_product_ids_test(self):
        for rule in self:
            rule.valid_product_ids_test = self.product_rule_rule

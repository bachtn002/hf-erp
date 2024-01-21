from odoo import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('is_loan')
    def _onchange_is_loan(self):
        if self.is_loan:
            self.type = 'service'
            self.categ_id = self.env.ref('to_loan_management.product_category_loan_interest')

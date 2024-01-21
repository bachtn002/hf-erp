from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_loan = fields.Boolean(string='Can be Loan')

    @api.constrains('is_loan', 'type')
    def _check_is_loan_vs_type(self):
        for r in self:
            if r.is_loan and r.type != 'service':
                raise UserError(_("Loan Product must be in the type of Service."))

    @api.onchange('is_loan')
    def _onchange_is_loan(self):
        if self.is_loan:
            self.type = 'service'
            self.categ_id = self.env.ref('to_loan_management.product_category_loan_interest')

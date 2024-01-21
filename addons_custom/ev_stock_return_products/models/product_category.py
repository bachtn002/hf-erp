# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_return_vendor_account_id = fields.Many2one('account.account', company_dependent=True,
                                                        string="Return Vendor Account",
                                                        domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]")

    property_customer_return_account_id = fields.Many2one('account.account', company_dependent=True,
                                                          string="Customer Return Account",
                                                          domain="['&', ('deprecated', '=', False), ('company_id', '=', current_company_id)]")
    active = fields.Boolean('Active Category', default=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_product_accounts(self, fiscal_pos=None):
        accounts = super(ProductTemplate, self).get_product_accounts(fiscal_pos=fiscal_pos)
        accounts.update({
                            'return_vendor_account': self.categ_id.property_return_vendor_account_id.id if self.categ_id.property_return_vendor_account_id else False,
                            'customer_return_account': self.categ_id.property_customer_return_account_id.id if self.categ_id.property_customer_return_account_id else False})
        return accounts

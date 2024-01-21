from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class NumberSearchLimit(models.TransientModel):
    _inherit = 'res.config.settings'
    x_number_search_limit = fields.Integer(related='company_id.x_number_search_limit',
                                           string=_('Number Search Customer Limit'), readonly=False)
    x_apply_fix_customer = fields.Boolean(related='company_id.x_apply_fix_customer',
                                           string=_('Apply fix customer'), readonly=False)

    @api.constrains('x_number_search_limit')
    def add_x_number_search_limit(self):
        if self.x_number_search_limit <= 0 or self.x_number_search_limit > 15:
            raise UserError(_('Number Search Customer Limit Error'))
        pos_configs = self.env['pos.config'].search([])
        for pos in pos_configs:
            pos.x_number_search_limit = self.x_number_search_limit

    @api.constrains('x_apply_fix_customer')
    def add_x_apply_fix_customer(self):
        pos_configs = self.env['pos.config'].search([])
        for pos in pos_configs:
            pos.x_apply_fix_customer = self.x_apply_fix_customer

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_revenue_accounting_by_product = fields.Boolean(related='company_id.x_revenue_accounting_by_product', string='Revenue accounting by product', readonly=False)
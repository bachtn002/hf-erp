# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SearchLoyaltyPoints(models.Model):
    _inherit = 'res.partner'

    def search_loyalty_points(self, id):
        partner = self.env['res.partner'].search([('id', '=', id)])
        return partner.loyalty_points
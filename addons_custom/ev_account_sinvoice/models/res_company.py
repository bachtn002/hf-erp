# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    number_pos_per_lot = fields.Integer('Number Pos Order Per Lot', default=50)
    sinvoice_production_url = fields.Char('SInvoice Production Url')
    sinvoice_username = fields.Char('SInvoice Username')
    sinvoice_password = fields.Char('SInvoice Password')
    sinvoice_search_url = fields.Char('SInvoice Search Url')

    sinvoice_type = fields.Char(string='SInvoice Type', help='Invoice type code, eg: 1, 2, 3, or 4')
    sinvoice_template_code = fields.Char(string='SInvoice Template Code', size=20, help='Invoice template symbol, eg: 0/001')
    sinvoice_series = fields.Char(string='SInvoice Series', size=7, help='Invoice symbol, eg: K23TAA')
    res_partner_bank_id = fields.Many2one('res.partner.bank', string='Partner Bank')


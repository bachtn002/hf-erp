# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosShop(models.Model):
    _inherit = 'pos.shop'

    product_ids = fields.Many2many('product.template', 'product_shop_rel', 'pos_shop_id', 'product_id',
                                   string='Product Template', copy=True, domain=[('active','=',True),('sale_ok', '=', True),('available_in_pos','=',True)])
    
    def open_import_product(self):
        return {
            'name': 'Import file Product',
            'type': 'ir.actions.act_window',
            'res_model': 'import.xls.wizard.product',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'current_id': self.id},
        }
    
    def get_import_product_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_product_shop_config/static/xls/imp_sanpham.xlsx'
        }

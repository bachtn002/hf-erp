# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    is_combo_line = fields.Boolean(string="Is Combo Order line", default=False)
    tech_combo_data = fields.Char(string="Tech Combo Info")
    combo_product_id = fields.Many2one('product.product', string="Combo Product Id")
    is_main_combo_product = fields.Boolean(string="Is Main Combo Product", default=False)

    def _export_for_ui(self, orderline):
        res = super(PosOrderLine, self)._export_for_ui(orderline)
        try:
            tech_combo_data = eval(orderline.tech_combo_data)
        except:
            _logger.error(f"Wrong format tech_combo_data of line {orderline.id}: {orderline.tech_combo_data}")
            tech_combo_data = []
        res.update({
            'combo_prod_info': tech_combo_data,
            'x_is_combo': True if len(tech_combo_data) > 0 else False
        })
        return res

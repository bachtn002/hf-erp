# -*- coding: utf-8 -*-
# Created by hoanglv at 2/9/2020

from odoo import api, fields, models
from functools import partial

import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        new_order_line = res.get('lines', [])
        process_line = partial(self.env['pos.order.line']._order_line_fields)
        order_lines = [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False
        if order_lines:
            for order_line in order_lines:
                if 'tech_combo_data' in order_line[2]:
                    new_order_line[order_lines.index(order_line)][2].update({
                        'is_main_combo_product': True,
                        'is_combo_line': False
                    })
                    own_pro_list = order_line[2]['tech_combo_data'] if order_line[2]['tech_combo_data'] else False
                    if own_pro_list:
                        for own in own_pro_list:
                            vals = {
                                'qty': own['qty'] * order_line[2]['qty'],
                                'price_unit': 0,
                                'price_subtotal': 0,
                                'price_subtotal_incl': 0,
                                'discount': 0,
                                'product_id': own['product']['id'],
                                'tax_ids': [(6, 0, [])],
                                'pack_lot_ids': [],
                                'full_product_name': own['product']['display_name'],
                                # 'note': '',
                                'name': order_line[2]['name'],
                                'is_combo_line': True,
                                'combo_product_id': order_line[2]['product_id']
                            }
                            new_order_line.append([0, 0, vals])
        res.update({
            'lines': new_order_line,
        })
        return res

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        res.update({
            'lines': [[0, 0, line] for line in order.lines.filtered(lambda l: l.tech_combo_data).export_for_ui()],
        })
        return res

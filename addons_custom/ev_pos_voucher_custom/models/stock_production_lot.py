# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class StockProductLot(models.Model):
    _inherit = 'stock.production.lot'

    # kiểm tra các cửa hàng được áp dụng có thể sử dụng được phiếu mua hàng
    # Kiểm tra phiếu mua hàng có được áp dụng cùng các CTKM hay không
    def _check_code_payment_from_ui(self, lot_name, customer_id=False, amount_due=1, config_id=False, promotion=False):
        data = {}
        # code = lot_name.strip().upper()
        code = lot_name.strip()
        lot_id = self.search([('name', '=', code)], limit=1)
        config = []
        if lot_id:
            if lot_id.x_release_id.sudo().config_ids:
                for item in lot_id.x_release_id.sudo().config_ids:
                    config.append(item.id)
            else:
                config_ids = self.env['pos.config'].search([('company_id', '=', self.env.company.id)])
                for item in config_ids:
                    config.append(item.id)
            if config_id not in config:
                data['type'] = 'not_config'
                data['message'] = 'Phiếu mua hàng không được áp dụng tại cửa hàng. Vui lòng kiểm tra lại!'
                return data
            if not lot_id.x_release_id.apply_promotion:
                if promotion:
                    data['type'] = 'promotion'
                    data['message'] = 'Phiếu mua hàng không được áp dụng cùng với các CTKM khác. Vui lòng kiểm tra lại!'
                return data
        return super(StockProductLot, self)._check_code_payment_from_ui(lot_name, customer_id, amount_due, config_id,
                                                                        promotion)

    # Kiểm tra giới hạn phiếu mua hàng được sử dụng trên đơn
    def _compute_amount_payment(self, lot_id, products, payments, amount_total, amount_due):
        if lot_id.x_release_id.limit_voucher:
            data = []
            product_ids = []
            for payment in payments:
                # code = payment['lot_name'].strip().upper()
                code = payment['lot_name'].strip()
                product_id = self.search([('name', '=', code)], limit=1).product_id.id
                if product_id not in product_ids:
                    product_ids.append(product_id)
                    data.append({'id': product_id,
                                 'qty': 1})
                else:
                    for item in data:
                        if product_id == item['id']:
                            item['qty'] += 1
            for i in data:
                if i['id'] == lot_id.product_id.id:
                    if i['qty'] >= lot_id.x_release_id.limit_qty:
                        return {
                            'type': 'limited',
                            'message': 'Bạn đã sử dụng hết số lượng phiếu mua hàng cùng loại được cho phép trên đơn!'
                        }
        return super(StockProductLot, self)._compute_amount_payment(lot_id, products, payments, amount_total,
                                                                    amount_due)

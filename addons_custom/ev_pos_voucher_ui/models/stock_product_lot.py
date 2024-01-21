# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class StockProductLot(models.Model):
    _inherit = 'stock.production.lot'

    def _check_code_payment_from_ui_if_modify(self, lot_name, customer_id=False, amount_due=1, config_id=False,
                                              promotion=False):
        data = {}
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
        return data

    def _check_code_from_ui_validate_if_modify_quantity(self, lot_name, customer_id=False, amount_due=1,
                                                        config_id=False,
                                                        promotion=False):
        data = {}
        arr_product_release = []
        for code in lot_name:
            lot_id = self.search([('name', '=', code)], limit=1)
            product_release = lot_id.x_release_id
            if product_release not in arr_product_release:
                arr_product_release.append(product_release)
        for product_release in arr_product_release:
            code_in_lotname = []
            for code in lot_name:
                lot_id = self.search([('name', '=', code)], limit=1)
                if lot_id.x_release_id.id == product_release.id:
                    code_in_lotname.append(code)
            if len(code_in_lotname) > product_release.limit_qty:
                return {
                    'type': 'limited',
                    'message': 'Bạn đã sử dụng hết số lượng phiếu mua hàng cùng loại được cho phép trên đơn!'
                }
        return data

    def check_code_from_ui_validate_if_modify(self, list_voucher_to_payment, customer_id, config_id, promotion):
        date_check_quantity = self._check_code_from_ui_validate_if_modify_quantity(list_voucher_to_payment, customer_id,
                                                                                   config_id=config_id,
                                                                                   promotion=promotion)
        if date_check_quantity:
            return date_check_quantity
        for voucher_to_payment in list_voucher_to_payment:
            data = self._check_code_payment_from_ui_if_modify(voucher_to_payment, customer_id, config_id=config_id,
                                                              promotion=promotion)
            if 'message' in data:
                return data
        return {}

# -*- coding: utf-8 -*-

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response
from odoo.http import Controller, route, request
from odoo import _
from datetime import datetime


def res(remote_ip=None, data=None, params=None, mesg=None, record=[]):
    unlink(record)
    Configs._set_log_api(remote_ip, '/sale_online/create', 'Đồng bộ đơn online miniapp', params, '400', mesg)
    return Response.error(mesg, data, code='400').to_json()


def unlink(record):
    for i in record:
        i.sudo().unlink()


class ApiCreateSaleOnline(Controller):
    @route('/sale_online/create', methods=['POST'], type='json', auth='public', cors='*', csrf=False)
    def api_create_sale_online(self):
        params = request.params
        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)
        if not is_ip_valid:
            mesg = 'YOUR_IP_ADDRESS_NOT_ALLOWED_TO_ACCESS_API'
            return res(remote_ip, None, params, mesg)
        if 'token_connect_api' not in params or not params['token_connect_api']:
            mesg = 'TOKEN_CONNECT_API_INVALID'
            return res(remote_ip, None, params, mesg)
        api_config = Configs._get_api_config(params['token_connect_api'])
        if not api_config:
            mesg = 'TOKEN_CONNECT_API_INVALID'
            return res(remote_ip, None, params, mesg)
        record_do_unlink = []
        try:
            general_info = params['order_detail']['general_info']
            item_info = params['order_detail']['item_info']
            promotion_info = params['order_detail']['promotion_info']
            payment_info = params['order_detail']['payment_info']
            discount_on_prod = promotion_info['discount_on_product']
            discount_on_bill = promotion_info['discount_on_bill']
            sale_online_record = None
            if not general_info['customer']:
                return res(remote_ip, None, params, mesg='INVALID_CUSTOMER')
            if not general_info['address']:
                return res(remote_ip, None, params, mesg='INVALID_ADDRESS')
            partner_id = request.env['res.partner'].sudo().search(
                [('active', '=', True), ('phone', '=', general_info['phone'])], limit=1).id
            pos_shop = request.env['pos.shop'].sudo().search([('code', '=', general_info['pos_shop'])], limit=1)
            if pos_shop:
                pos_config_id = pos_shop.pos_config_ids[0].id
            else:
                return res(remote_ip, None, params, mesg='INVALID_POS_SHOP')
            source_order = request.env['source.order'].sudo().search([('code', '=', general_info['source_order'])],
                                                                     limit=1)
            if source_order:
                source_order_id = source_order.id
            else:
                return res(remote_ip, None, params, mesg='INVALID_SOURCE_ORDER')
            pos_channel = request.env['pos.channel'].sudo().search(
                [('code', '=', general_info['pos_channel'])], limit=1)
            if pos_channel:
                pos_channel_id = pos_channel.id
            else:
                return res(remote_ip, None, params, mesg='INVALID_POS_CHANNEL')
            if 'loyalty_point_redeem' in promotion_info and not isinstance(promotion_info['loyalty_point_redeem'], int):
                return res(remote_ip, None, params, mesg='INVALID_PROMOTION_INFO__LOYALTY_POINT_REDEEM')
            try:
                datetime.strptime(general_info['date'], '%Y-%m-%d')
            except:
                return res(remote_ip, None, params, mesg='INVALID_DATE')
            if 'sinvoice_info' not in general_info:
                return res(remote_ip, None, params, mesg='INVALID_PARAMETER_SINVOICE_INFO')
            if 'buyer_not_get_invoice' not in general_info['sinvoice_info']:
                return res(remote_ip, None, params, mesg='INVALID_SINVOICE_INFO__BUYER_NOT_GET_INVOICE')
            if not general_info['sinvoice_info']['buyer_not_get_invoice']:
                if 'sinvoice_vat' not in general_info['sinvoice_info'] \
                        or 'sinvoice_company_name' not in general_info['sinvoice_info'] \
                        or 'sinvoice_address' not in general_info['sinvoice_info'] \
                        or 'sinvoice_email' not in general_info['sinvoice_info']:
                    return res(remote_ip, None, params, mesg='INVALID_PARAMETER_SINVOICE_INFO')
                if not general_info['sinvoice_info']['sinvoice_vat'] \
                        or not general_info['sinvoice_info']['sinvoice_company_name'] \
                        or not general_info['sinvoice_info']['sinvoice_address'] \
                        or not general_info['sinvoice_info']['sinvoice_email']:
                    mesg = 'INVALID_PARAMETER_SINVOICE_INFO'
                    return res(remote_ip, None, params, mesg)
            if 'home_delivery' not in general_info:
                return res(remote_ip, None, params, mesg='INVALID_HOME_DELIVERY')
            if general_info['home_delivery']:
                if not general_info['delivery_info']['receiver'] \
                        or not general_info['delivery_info']['receiver_phone'] \
                        or not general_info['delivery_info']['x_distance'] \
                        or not general_info['delivery_info']['address_delivery'] \
                        or not general_info['delivery_info']['lat'] \
                        or not general_info['delivery_info']['long']:
                    mesg = 'INVALID_PARAMETER_DELIVERY_INFO'
                    return res(remote_ip, None, params, mesg)
            if request.env['sale.online'].sudo().search([('ref_order', '=', general_info['ref_order'])]):
                return res(remote_ip, None, params, mesg='INVALID_GENERAL_INFO__REF_ORDER_ALREADY_EXISTS')
            val = {
                'ref_order': general_info['ref_order'],
                'date': datetime.strptime(general_info['date'], '%Y-%m-%d'),
                'source_order_id': source_order_id,
                'pos_config_id': pos_config_id,
                'note': general_info['note'],
                'home_delivery': general_info['home_delivery'],
                'receiver': general_info['delivery_info']['receiver'],
                'receiver_phone': general_info['delivery_info']['receiver_phone'],
                'x_distance': general_info['delivery_info']['x_distance'],
                'address_delivery': general_info['delivery_info']['address_delivery'],
                'lat': general_info['delivery_info']['lat'],
                'long': general_info['delivery_info']['long'],
                'phone': general_info['phone'],
                'customer': general_info['customer'],
                'address': general_info['address'],
                'partner_id': partner_id,
                'pos_channel_id': pos_channel_id,
                'state': 'draft',
                'sinvoice_vat': general_info['sinvoice_info']['sinvoice_vat'],
                'sinvoice_company_name': general_info['sinvoice_info']['sinvoice_company_name'],
                'sinvoice_address': general_info['sinvoice_info']['sinvoice_address'],
                'sinvoice_email': general_info['sinvoice_info']['sinvoice_email'],
                'buyer_not_get_invoice': general_info['sinvoice_info']['buyer_not_get_invoice'],
                'loyalty_point_redeem': promotion_info['loyalty_point_redeem'],
                'is_created_by_api': True,
            }
            try:
                sale_online_record = request.env['sale.online'].sudo().create(val)
                record_do_unlink.append(sale_online_record)
            except Exception as ex:
                mesg = 'INVALID_PARAMETER_GENERAL_INFO'
                return res(remote_ip, data={'message_error': str(ex)}, params=params, mesg=mesg)
            if sale_online_record:
                if not partner_id:
                    sale_online_record.sudo().create_customer()

                # item_info
                if item_info:
                    for item in item_info:
                        if 'quantity' not in item or (item['quantity'] and not isinstance(item['quantity'], (float, int))):
                            return res(remote_ip, None, params, mesg='INVALID_ITEM_INFO__QUANTITY', record=record_do_unlink)
                        if 'price' not in item or (not isinstance(item['price'], (float, int))):
                            return res(remote_ip, None, params, mesg='INVALID_ITEM_INFO__PRICE', record=record_do_unlink)
                        if 'product_code' not in item:
                            return res(remote_ip, None, params, mesg='INVALID_ITEM_INFO__PRODUCT_CODE', record=record_do_unlink)
                        product = request.env['product.template'].sudo().search([('default_code', '=', item['product_code'])], limit=1)
                        if product:
                            product_id = product.id
                        else:
                            return res(remote_ip, None, params, mesg='INVALID_ITEM_INFO__PRODUCT_CODE', record=record_do_unlink)
                        product_uom = request.env['uom.uom'].sudo().search([('name', '=', item['dvt'])], limit=1)
                        if product_uom:
                            product_uom_id = product_uom.id
                        else:
                            return res(remote_ip, None, params, mesg='INVALID_ITEM_INFO__DVT', record=record_do_unlink)

                        line_order_line = {
                            'sale_online_id': sale_online_record.id,
                            'product_id': product_id,
                            'quantity': item['quantity'],
                            'uom': product_uom_id,
                            'price': item['price'],
                        }
                        try:
                            sale_online_order_line_record = request.env['sale.online.order.line'].sudo().create(line_order_line)
                            record_do_unlink.append(sale_online_order_line_record)
                        except Exception as ex:
                            mesg = 'INVALID_PARAMETER_ITEM_INFO'
                            return res(remote_ip, data={'message_error': str(ex)}, params=params, mesg=mesg, record=record_do_unlink)
                else:
                    return res(remote_ip, None, params, mesg='INVALID_PARAMS__ITEM_INFO', record=record_do_unlink)
                # payment_info
                if payment_info:
                    for line in payment_info:
                        if 'amount' not in line or (line['amount'] and not isinstance(line['amount'], (float, int))):
                            return res(remote_ip, None, params, mesg='INVALID_PAYMENT_INFO__AMOUNT', record=record_do_unlink)

                        if 'payment_method_id' not in line:
                            return res(remote_ip, None, params, mesg='INVALID_PAYMENT_INFO__PAYMENT_METHOD_ID',
                                       record=record_do_unlink)
                        payment_method_id = line['payment_method_id']
                        if not request.env['pos.payment.method'].sudo().search([('id', '=', payment_method_id)]):
                            return res(remote_ip, None, params, mesg='INVALID_PAYMENT_INFO__PAYMENT_METHOD_ID', record=record_do_unlink)
                        line_pay_info = {
                            'payment_method_id': payment_method_id,
                            'amount': line['amount'],
                            'sale_online_id': sale_online_record.id,
                        }
                        try:
                            sale_online_payment_info_record = request.env['sale.online.payment.info'].sudo().create(line_pay_info)
                            record_do_unlink.append(sale_online_payment_info_record)
                        except Exception as ex:
                            mesg = _('INVALID_PARAMETER_PAYMENT_INFO')
                            return res(remote_ip, data={'message_error': str(ex)}, params=params, mesg=mesg, record=record_do_unlink)
                # else:
                #     return res(remote_ip, None, params, mesg='INVALID_PARAMS__PAYMENT_INFO', record=record_do_unlink)

                # discount_on_product
                if discount_on_prod:
                    for prod in discount_on_prod:
                        if 'product_code' not in prod:
                            return res(remote_ip, None, params, mesg='INVALID_DISCOUNT_ON_PRODUCT__PRODUCT_CODE', record=record_do_unlink)
                        product = request.env['product.template'].sudo().search([('default_code', '=', prod['product_code'])], limit=1)
                        if not product:
                            return res(remote_ip, None, params, mesg='INVALID_DISCOUNT_ON_PRODUCT__PRODUCT_CODE', record=record_do_unlink)
                        if 'discount' in prod and not isinstance(prod['discount'], (float, int)):
                            return res(remote_ip, None, params, mesg='INVALID_DISCOUNT_ON_PRODUCT__DISCOUNT', record=record_do_unlink)
                        val = {
                            'product_code': prod['product_code'],
                            'discount_amount': prod['discount'],
                            'promotion_code': prod['promotion_code'],
                            'promotion_id': prod['promotion_id'],
                            'discount_type': 'on_product',
                            'sale_online_id': sale_online_record.id
                        }
                        try:
                            dis_on_prod = request.env['sale.online.discount'].sudo().create(val)
                            record_do_unlink.append(dis_on_prod)

                            # update discount, x_is_price_promotion in order line
                            for p in sale_online_record.order_line_ids:
                                if prod['product_code'] == p.product_id.default_code:
                                    p.discount = p.x_is_price_promotion = float(prod['discount'])
                                    p.promotion_code = prod['promotion_code']
                                    p.amount_subtotal_incl = p.amount - p.discount

                        except Exception as ex:
                            mesg = 'INVALID_PARAMETER_DISCOUNT_ON_PRODUCT'
                            return res(remote_ip, data={'message_error': str(ex)}, params=params, mesg=mesg, record=record_do_unlink)

                # discount_on_bill
                if discount_on_bill:
                    for item in discount_on_bill:
                        if 'discount' in item and not isinstance(item['discount'], (float, int)):
                            return res(remote_ip, None, params, mesg='INVALID_DISCOUNT_ON_BILL__DISCOUNT', record=record_do_unlink)
                        val = {
                            'discount_amount': item['discount'],
                            'promotion_code': item['promotion_code'],
                            'promotion_id': item['promotion_id'],
                            'discount_type': 'on_bill',
                            'sale_online_id': sale_online_record.id,
                        }
                        try:
                            dis_on_bill = request.env['sale.online.discount'].sudo().create(val)
                            record_do_unlink.append(dis_on_bill)
                        except Exception as ex:
                            mesg = 'INVALID_PARAMETER_DISCOUNT_ON_BILL'
                            return res(remote_ip, data={'message_error': str(ex)}, params=params, mesg=mesg, record=record_do_unlink)

            # success all
            sale_online_record.send_sale_request()
            total_discount_on_bill = 0
            promotion_code = ''
            discounts_on_bill = sale_online_record.sale_online_discount_ids.filtered(lambda x: x.discount_type == 'on_bill')
            for item in discounts_on_bill:
                total_discount_on_bill += float(item.discount_amount)
                if item.promotion_code != '':
                    promotion_code += (item.promotion_code + ', ')
            sale_online_record.total_discount_on_bill = total_discount_on_bill
            sale_online_record.promotion_code = promotion_code.strip()[:-1]

            Configs._set_log_api(remote_ip, '/sale_online/create', 'Đồng bộ đơn online miniapp', params, '200', None)
            return Response.success(None, data={'sale_online_id': sale_online_record.id}).to_json()
        except Exception as ex:
            if record_do_unlink:
                unlink(record_do_unlink)
            mesg = 'INTERNAL_SERVER_ERROR'
            Configs._set_log_api(remote_ip, '/sale_online/create', 'Đồng bộ đơn online miniapp', params, '500', str(ex))
            return Response.error(message=mesg, data={'message_error': str(ex)}, code='500').to_json()

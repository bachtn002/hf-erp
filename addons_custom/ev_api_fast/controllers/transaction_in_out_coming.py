# -*- coding: utf-8 -*-
import json
import logging
import psycopg2
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

import odoo
from odoo import http, tools, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

from ..helpers import Configs
from ..helpers.Response import Response


class ApiTransactionInOutComing(http.Controller):

    @http.route('/transaction_incoming', methods=['POST'], type='json', auth='public')
    def get_transaction_incoming(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/transaction_incoming', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/transaction_incoming', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'from_date' not in params:
            mesg = _("Missing from_date!")
            Configs._set_log_api(remote_ip, '/transaction_incoming', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'to_date' not in params:
            mesg = _("Missing to_date!")
            Configs._set_log_api(remote_ip, '/transaction_incoming', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        # if 'shop' not in params:
        #     mesg = _("Missing shop!")
        #     Configs._set_log_api(remote_ip, '/transaction_incoming', '', params, '400', mesg)
        #     return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        from_date = datetime.strptime(params['from_date'], '%d-%m-%Y').date()
        to_date = datetime.strptime(params['to_date'], '%d-%m-%Y').date()

        max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')
        if from_date + relativedelta(days=int(max_date)) < to_date:
            to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')
        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)

        api_id = Configs._get_api_config(token)

        shop = 0
        if 'shop' in params:
            shop_code = params.get('shop')
            shop_id = http.request.env['account.analytic.account'].sudo().search([('code', '=', shop_code)], limit=1)
            shop = shop_id.id if shop_id else 0

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/transaction_incoming', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()
        elif api_id:

            # if not shop_id:
            #     mesg = _("There is no shop matching with code %s") % shop_code
            #     Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '403', mesg)
            #     return Response.error(mesg, data={}, code='403').to_json()

            check_connect = True
            try:
                conn = psycopg2.connect(host=api_id.connection_id.name, database=api_id.connection_id.database,
                                        user=api_id.connection_id.user, password=api_id.connection_id.password,
                                        port=api_id.connection_id.port)
            except Exception as e:
                check_connect = False

            if not check_connect and api_id.preventive:
                try:
                    conn = psycopg2.connect(host=api_id.connection_preventive.name,
                                            database=api_id.connection_preventive.database,
                                            user=api_id.connection_preventive.user,
                                            password=api_id.connection_preventive.password,
                                            port=api_id.connection_preventive.port)
                except Exception as e:
                    Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '403', e)
                    return Response.error(str(e), data={}).to_json()
            elif not check_connect and not api_id.preventive:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '403', e)
                return Response.error().to_json()

            cur = conn.cursor()
            query = """
                SELECT a.id as                            stt_rec,
                       b.name                             so_ct,
                       to_char(b.date_done + INTERVAL '7 hours', 'dd/mm/yyyy') ngay_ct,
                        case
                           when l.x_note_in_out_comming is null then sl.name
                           when Length(RTRIM(l.x_note_in_out_comming)) = 0 then  sl.name
                           else l.x_note_in_out_comming end                    dien_giai,
                       d.code                             ma_kh,
                       c.default_code                     ma_vt,
                       a.qty_done                         so_luong,
                       l.price_unit                       don_gia,
                       a.qty_done * l.price_unit          tien,
                       g.code                             ma_nx,
                       d.code                             ma_bp,
                       k.code                             ma_phi
                from stock_move_line a
                         left join stock_picking b on b.id = a.picking_id
                         left join product_product c on c.id = a.product_id
                         left join account_analytic_account d on d.id = b.x_analytic_account_id
                         left join account_expense_item k on k.id = b.x_account_expense_item
                         left join stock_move l on l.id = a.move_id
                         join stock_location sl on sl.id = a.location_id
                         left join account_account g on g.id = sl.valuation_in_account_id
                where b.x_type_other = 'incoming'
                  and (d.id = %s or %s = 0)
                  and b.date_done >= %s
                  and b.date_done <= %s
            """
            cur.execute(query, (shop, shop, global_from_date, global_to_date))

            data = cur.fetchall()
            total_record = len(data)

            def __get_data():
                for line in data:
                    yield {
                        'stt_rec': line[0],
                        'so_ct': line[1] or '',
                        'ngay_ct': line[2],
                        'dien_giai': line[3] or '',
                        'ma_kh': line[4] or '',
                        'ma_vt': line[5] or '',
                        'so_luong': line[6],
                        'don_gia': line[7],
                        'tien': line[8],
                        'ma_nx': line[9] or '',
                        'ma_bp': line[10] or '',
                        'ma_phi': line[11] or ''
                    }

            cur.close()
            try:
                mesg = _('Get data successfully!')
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "record_total": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '404', e)
                return Response.error(str(e), data={}).to_json()

    @http.route('/transaction_outgoing', methods=['POST'], type='json', auth='public')
    def get_transaction_outgoing(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/transaction_outgoing', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/transaction_outgoing', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'from_date' not in params:
            mesg = _("Missing from_date!")
            Configs._set_log_api(remote_ip, '/transaction_outgoing', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'to_date' not in params:
            mesg = _("Missing to_date!")
            Configs._set_log_api(remote_ip, '/transaction_outgoing', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        # if 'shop' not in params:
        #     mesg = _("Missing shop!")
        #     Configs._set_log_api(remote_ip, '/transaction_outgoing', '', params, '400', mesg)
        #     return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        from_date = datetime.strptime(params['from_date'], '%d-%m-%Y').date()
        to_date = datetime.strptime(params['to_date'], '%d-%m-%Y').date()

        max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')
        if from_date + relativedelta(days=int(max_date)) < to_date:
            to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')
        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)

        api_id = Configs._get_api_config(token)
        shop = 0
        if 'shop' in params:
            shop_code = params.get('shop')
            shop_id = http.request.env['account.analytic.account'].sudo().search([('code', '=', shop_code)], limit=1)
            shop = shop_id.id if shop_id else 0

        # if not shop_id:
        #     mesg = _("There is no shop matching with code %s") % shop_code
        #     Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '404', mesg)
        #     return Response.error(mesg, data={}, code='404').to_json()
        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/transaction_outgoing', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()
        elif api_id:
            check_connect = True
            try:
                conn = psycopg2.connect(host=api_id.connection_id.name, database=api_id.connection_id.database,
                                        user=api_id.connection_id.user, password=api_id.connection_id.password,
                                        port=api_id.connection_id.port)
            except Exception as e:
                check_connect = False

            if not check_connect and api_id.preventive:
                try:
                    conn = psycopg2.connect(host=api_id.connection_preventive.name,
                                            database=api_id.connection_preventive.database,
                                            user=api_id.connection_preventive.user,
                                            password=api_id.connection_preventive.password,
                                            port=api_id.connection_preventive.port)
                except Exception as e:
                    Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '403', e)
                    return Response.error(str(e), data={}).to_json()
            elif not check_connect and not api_id.preventive:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '403', e)
                return Response.error().to_json()

            cur = conn.cursor()
            query = """
                   SELECT
                       a.id as                            stt_rec,
                       b.name                             so_ct,
                       to_char(b.date_done + INTERVAL '7 hours', 'dd/mm/yyyy') ngay_ct,
                        case
                           when l.x_note_in_out_comming is null then sl.name
                           when Length(RTRIM(l.x_note_in_out_comming)) = 0 then  sl.name
                           else l.x_note_in_out_comming end                    dien_giai,
                       d.code                             ma_kh,
                       c.default_code                     ma_vt,
                       a.qty_done                         so_luong,
                       n.unit_cost                        don_gia,
                       a.qty_done * n.unit_cost           tien,
                       g.code                             ma_nx,
                       d.code                             ma_bp,
                       k.code                             ma_phi
                    from stock_move_line a
                         left join stock_picking b on b.id = a.picking_id
                         left join product_product c on c.id = a.product_id
                         left join account_analytic_account d on d.id = b.x_analytic_account_id
                         left join account_expense_item k on k.id = b.x_account_expense_item
                         left join stock_move l on l.id = a.move_id
                         left join stock_valuation_layer n on n.stock_move_id = a.move_id
                         join stock_location sl on sl.id = a.location_dest_id
                         left join account_account g on g.id = sl.valuation_in_account_id
                    where b.x_type_other = 'outgoing'
                          and (d.id = %s or %s = 0)
                          and b.date_done >= %s
                          and b.date_done <= %s
               """
            cur.execute(query, (shop, shop, global_from_date, global_to_date))
            data = cur.fetchall()
            total_record = len(data)

            def __get_data():
                for line in data:
                    yield {
                        'stt_rec': line[0],
                        'so_ct': line[1] or '',
                        'ngay_ct': line[2] or '',
                        'dien_giai': line[3] or '',
                        'ma_kh': line[4] or '',
                        'ma_vt': line[5] or '',
                        'so_luong': line[6],
                        'don_gia': line[7],
                        'tien': line[8],
                        'ma_nx': line[9] or '',
                        'ma_bp': line[10] or '',
                        'ma_phi': line[11] or ''
                    }

            cur.close()
            try:
                mesg = _('Get data successfully!')
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "record_total": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '404', e)
                return Response.error(str(e), data={}).to_json()

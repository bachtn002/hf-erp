# -*- coding: utf-8 -*-
import logging
import psycopg2
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import http, tools, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

from ..helpers import Configs
from ..helpers.Response import Response


class ProductProduct(http.Controller):

    @http.route('/product_product', methods=['POST'], type='json', auth='public')
    def get_product_product(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/product_product', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/product_product', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'from_date' not in params:
            mesg = _("Missing from_date!")
            Configs._set_log_api(remote_ip, '/product_product', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'to_date' not in params:
            mesg = _("Missing to_date!")
            Configs._set_log_api(remote_ip, '/product_product', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        from_date = datetime.strptime(params['from_date'], '%d-%m-%Y').date()
        to_date = datetime.strptime(params['to_date'], '%d-%m-%Y').date()

        # max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')
        # if from_date + relativedelta(days=int(max_date)) < to_date:
        #     to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')
        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)

        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/product_product', '', params, '401', mesg)
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
                    Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '504', e)
                    return Response.error(str(e), data={}).to_json()
            elif not check_connect and not api_id.preventive:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '400', e)
                return Response.error().to_json()

            cur = conn.cursor()
            query = """
                SELECT b.id stt_rec,
                        b.default_code         ma_vt,
                       a.name                 ten_vt,
                       ''                 ten_vt2,
                       c.name                 dvt,
                       case
                           when a.type = 'product' then 1
                           else 0 end      as vt_ton_kho,
                       1                      gia_ton,
                       'Hàng hóa'             loai_vt,
                       e.name                 ma_thue,
                       case
                           when f.parent_id is not null then g.name
                           else f.name end as nh_vt,
                       case
                           when b.active = True then 1
                           else 0 end      as status,
                       f.id                   categ_id,
                       a.available_in_pos     is_available_pos
                from product_template a
                         left join product_product b on a.id = b.product_tmpl_id
                         left join uom_uom c on c.id = a.uom_id
                         left join product_taxes_rel d on d.prod_id = a.id
                         left join account_tax e on e.id = d.tax_id
                         left join product_category f on f.id = a.categ_id
                         left join product_category g on g.id = f.parent_id
                where a.write_date >= %s
                      and a.write_date <= %s
            """
            cur.execute(query, (global_from_date, global_to_date))

            data = cur.fetchall()
            total_record = len(data)

            def __get_data():
                for line in data:
                    categ_id = http.request.env['product.category'].sudo().search([('id', '=', line[10])])

                    yield {
                        'stt_rec': line[0],
                        'ma_vt': line[1] or '',
                        'ten_vt': line[2] or '',
                        'ten_vt2': line[3] or '',
                        'dvt': line[4] or '',
                        'vt_ton_kho': line[5],
                        'gia_ton': line[6],
                        'loai_vt': line[7] or '',
                        'ma_thue': line[8] or '',
                        'tk_vt': categ_id.property_stock_valuation_account_id.code or '',
                        'tk_gv': categ_id.property_stock_account_output_categ_id.code or '',
                        'tk_dt': categ_id.property_account_income_categ_id.code or '',
                        'tk_tl': categ_id.property_customer_return_account_id.code or '',
                        'tk_cl_vt': categ_id.property_account_creditor_price_difference_categ.code or '',
                        'tk_ck': '5111',
                        'nh_vt': line[9] or '',
                        'ghi_chu': '' or '',
                        'status': line[10],
                        'is_available_pos': line[12],
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
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '504', e)
                return Response.error(str(e), data={}).to_json()

    @http.route('/product_combo', methods=['POST'], type='json', auth='public')
    def get_product_combo(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/product_process_rule/materials', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/product_combo', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'from_date' not in params:
            mesg = _("Missing from_date!")
            Configs._set_log_api(remote_ip, '/product_combo', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'to_date' not in params:
            mesg = _("Missing to_date!")
            Configs._set_log_api(remote_ip, '/product_combo', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        from_date = datetime.strptime(params['from_date'], '%d-%m-%Y').date()
        to_date = datetime.strptime(params['to_date'], '%d-%m-%Y').date()

        # max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')
        # if from_date + relativedelta(days=int(max_date)) < to_date:
        #     to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')
        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)

        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/product_combo', '', params, '401', mesg)
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
                    Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '504', e)
                    return Response.error(str(e), data={}).to_json()
            elif not check_connect and not api_id.preventive:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '400', e)
                return Response.error().to_json()

            cur = conn.cursor()
            query = """
                    SELECT a.id stt_rec,
                            e.default_code ma_sp,
                           e.name         ten_vt,
                           ''             ten_vt2,
                           d.name         dvt,
                           b.default_code ma_vt,
                           a.no_of_items  so_luong,
                           ''             ghi_chu
                    from product_combo a
                             left join product_product b on b.id = a.product_ids
                             left join product_template c on c.id = b.product_tmpl_id
                             left join product_template e on e.id = a.product_tmpl_id
                             left join uom_uom d on d.id = e.uom_id
                    where e.write_date >= %s
                      and e.write_date <= %s
                """
            cur.execute(query, (global_from_date, global_to_date))

            data = cur.fetchall()
            total_record = len(data)

            def __get_data():
                for line in data:
                    yield {
                        'stt_rec': line[0],
                        'ma_sp': line[1] or '',
                        'ten_vt': line[2] or '',
                        'ten_vt2': line[3] or '',
                        'dvt': line[4] or '',
                        'ma_vt': line[5] or '',
                        'so_luong': line[6],
                        'ghi_chu': '',
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
                Configs._set_log_api(remote_ip, api_id.code, api_id.name, params, '504', e)
                return Response.error(str(e), data={}).to_json()

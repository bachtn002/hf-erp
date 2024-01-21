# -*- coding: utf-8 -*-
import psycopg2
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import http, _
from odoo.http import Controller, route

from ..helpers import Configs
from ..helpers.Response import Response


class PosOrderControllers(Controller):

    @route('/product_process_rule/materials', methods=['POST'], auth='public', type='json')
    def get_materials(self):
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
            Configs._set_log_api(remote_ip, '/product_process_rule/materials', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        api_config = Configs._get_api_config(params['token_connect_api'])

        from_date = datetime.strptime(http.request.params.get('from_date'), '%d-%m-%Y').date()
        to_date = datetime.strptime(http.request.params.get('to_date'), '%d-%m-%Y').date()

        # max_date = http.request.env['ir.config_parameter'].sudo().get_param('max_date_api')

        # if from_date + relativedelta(days=int(max_date)) < to_date:
        #     to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')
        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)

        if not api_config:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/product_process_rule/materials', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()

        if api_config:
            connection = api_config.connection_id
            check_connect = True
            try:
                conn = psycopg2.connect(host=connection.name, database=connection.database, user=connection.user,
                                        password=connection.password,
                                        port=connection.port)
            except Exception as e:
                check_connect = False
            if not check_connect and api_config.preventive:
                try:
                    conn = psycopg2.connect(host=api_config.connection_preventive.name,
                                            database=api_config.connection_preventive.database,
                                            user=api_config.connection_preventive.user,
                                            password=api_config.connection_preventive.password,
                                            port=api_config.connection_preventive.port)
                except Exception as e:
                    Configs._set_log_api(remote_ip, '/product_process_rule/materials', api_config.name, params, '504', str(e))
                    return Response.error(e, data={}).to_json()
            elif not check_connect and not api_config.preventive:
                mesg = _("An error occurred, please try again later")
                Configs._set_log_api(remote_ip, '/product_process_rule/materials', api_config.name, params, '400', mesg)
                return Response.error().to_json()
            # create a cursor
            cur = conn.cursor()
            # Execute a sql
            query = """
                SELECT a.id               stt_rec,
                       a.from_rule_id     ma_btp,
                       b.name             ten_vt,
                       d.name             dvt,
                       c.default_code     ma_vt,
                       a.qty              sl_nvl
                from product_process_rule_line a
                         join product_process_rule b on b.id = a.from_rule_id
                         join product_product c on c.id = a.product_id
                         join uom_uom d on d.id = a.uom_id
            
                where b.write_date >= %s
                      and b.write_date <= %s         
                """
            cur.execute(query, (global_from_date, global_to_date))

            materials = cur.fetchall()
            total_record = len(materials)
            def __get_data():
                for material in materials:
                    yield {
                        "stt_rec": material[0],
                        "ma_btp": material[1],
                        "ten_vt": material[2] or '',
                        "dvt": material[3] or '',
                        "ma_vt": material[4] or '',
                        "sl_nvl": material[5],
                    }

            # close the communication with the PostgreSQL
            cur.close()
            try:
                mesg = _("Get data successfully!")
                Configs._set_log_api(remote_ip, '/product_process_rule/materials', api_config.name, params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "record_total": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, '/product_process_rule/materials', api_config.name, params, '504', str(e))
                return Response.error(str(e), data={}).to_json()

    @route('/product_process_rule/products', methods=['POST'], auth='public', type='json')
    def get_products(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/product_process_rule/products', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip,'/product_process_rule/products', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        api_config = Configs._get_api_config(params['token_connect_api'])

        from_date = datetime.strptime(http.request.params.get('from_date'), '%d-%m-%Y').date()
        to_date = datetime.strptime(http.request.params.get('to_date'), '%d-%m-%Y').date()

        # max_date = http.request.env['ir.config_parameter'].sudo().get_param('max_date_api')

        # if from_date + relativedelta(days=int(max_date)) < to_date:
        #     to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')
        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)

        if not api_config:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/product_process_rule/products', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()

        if api_config:
            connection = api_config.connection_id
            check_connect = True
            try:
                conn = psycopg2.connect(host=connection.name, database=connection.database, user=connection.user,
                                        password=connection.password,
                                        port=connection.port)
            except Exception as e:
                check_connect = False
            if not check_connect and api_config.preventive:
                try:
                    conn = psycopg2.connect(host=api_config.connection_preventive.name,
                                            database=api_config.connection_preventive.database,
                                            user=api_config.connection_preventive.user,
                                            password=api_config.connection_preventive.password,
                                            port=api_config.connection_preventive.port)
                except Exception as e:
                    Configs._set_log_api(remote_ip, '/product_process_rule/products', api_config.name, params, '504', str(e))
                    return Response.error(e, data={}).to_json()
            elif not check_connect and not api_config.preventive:
                mesg = _("An error occurred, please try again later")
                Configs._set_log_api(remote_ip, '/product_process_rule/products', api_config.name, params, '400', mesg)
                return Response.error().to_json()
            # create a cursor
            cur = conn.cursor()
            # Execute a sql
            query = """
                    SELECT a.id            stt_rec,
                           a.to_rule_id    ma_btp,
                           b.name          ten_vt,
                           d.name          dvt,
                           c.default_code  ma_vt,
                           a.qty           so_luong,
                           a.percent       tl_gv,
                           a.error_percent tl_th
                    from product_process_rule_line a
                             join product_process_rule b on b.id = a.to_rule_id
                             join product_product c on c.id = a.product_id
                             join uom_uom d on d.id = a.uom_id
                    where b.write_date >= %s
                      and b.write_date <= %s    
                    """
            cur.execute(query, (global_from_date, global_to_date))

            products = cur.fetchall()
            total_record = len(products)

            def __get_data():
                for product in products:
                    yield {
                        "stt_rec": product[0],
                        "ma_btp": product[1],
                        "ten_vt": product[2] or '',
                        "dvt": product[3] or '',
                        "ma_vt": product[4] or '',
                        "so_luong": product[5],
                        "tl_gv": product[6],
                        "tl_th": product[7],
                    }

            # close the communication with the PostgreSQL
            cur.close()
            try:
                mesg = _("Get data successfully!")
                Configs._set_log_api(remote_ip, '/product_process_rule/products', api_config.name, params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "record_total": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, '/product_process_rule/products', api_config.name, params, '504', str(e))
                return Response.error(str(e), data={}).to_json()

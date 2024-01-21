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

    @http.route('/res_partner', methods=['POST'], type='json', auth='public')
    def get_res_partner(self):
        # Check connection and token to make valid connection
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/res_partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/res_partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'from_date' not in params:
            mesg = _("Missing from_date!")
            Configs._set_log_api(remote_ip, '/res_partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'to_date' not in params:
            mesg = _("Missing to_date!")
            Configs._set_log_api(remote_ip, '/res_partner', '', params, '400', mesg)
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
            Configs._set_log_api(remote_ip, '/res_partner', '', params, '401', mesg)
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
                       a.ref             ma_kh,
                       a.name            ten_kh,
                       ''            ten_kh2,
                       a.street          dia_chi,
                       a.vat             ma_so_thue,
                       case
                           when a.x_is_supplier = true then 1
                           else 0 end as cc_yn,
                       a.phone           dien_thoai,
                       a.email           email,
                       (SELECT acc_number
                        from res_partner_bank
                        where active = true
                          and partner_id = a.id
                        order by create_date asc
                        limit 1) tk_nh,
                       (SELECT c.name
                        from res_partner_bank b
                                 left join res_bank c on c.id = b.bank_id
                        where b.active = true
                          and b.partner_id = a.id
                        order by b.create_date asc
                        limit 1) ngan_hang,
                       ''                ghi_chu,
                       case
                           when a.active = True then 1
                           else 0 end as status
                from res_partner a
                where a.write_date >= %s
                      and a.write_date <= %s
                      and a.x_is_supplier = true
            """
            cur.execute(query, (global_from_date, global_to_date))

            data = cur.fetchall()
            total_record = len(data)

            def __get_data():
                for line in data:
                    yield {
                        'stt_rec': line[0],
                        'ma_kh': line[1] or "",
                        'ten_kh': line[2] or "",
                        'ten_kh2': line[3] or "",
                        'dia_chi': line[4] or "",
                        'ma_so_thue': line[5] or "",
                        'cc_yn': line[6] or "",
                        'dien_thoai': line[7] or "",
                        'email': line[8] or "",
                        'tk_nh': line[9] or "",
                        'ngan_hang': line[10] or "",
                        'ghi_chu': line[11] or "",
                        'status': line[12] or "",
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

# -*- coding: utf-8 -*-

import psycopg2
from odoo import http, _

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response


class ApiUom(http.Controller):

    @http.route('/uom_detail', methods=['POST'], type='json', auth='public')
    def get_detail_uom(self):
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/uom_detail', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/uom_detail', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/uom_detail', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()
        elif api_id:
            check_connect = True
            try:
                conn = psycopg2.connect(host=api_id.connection_id.name,
                                        database=api_id.connection_id.database,
                                        user=api_id.connection_id.user,
                                        password=api_id.connection_id.password,
                                        port=api_id.connection_id.port)
            except Exception as e:
                check_connect = False

            if not check_connect and api_id.preventive:
                try:
                    conn = psycopg2.connect(
                        host=api_id.connection_preventive.name,
                        database=api_id.connection_preventive.database,
                        user=api_id.connection_preventive.user,
                        password=api_id.connection_preventive.password,
                        port=api_id.connection_preventive.port)
                except Exception as e:
                    Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                         params, '504', e)
                    return Response.error(str(e), data={}).to_json()
            elif not check_connect and not api_id.preventive:
                mesg = _("Missing connection!")
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '400', mesg)
                return Response.error().to_json()
            from_date = params.get('from_date') or ''
            to_date = params.get('to_date') or ''

            cur = conn.cursor()
            query = """
                SELECT uu.name, uu.id, 
                        CAST(uu.active AS INT) active, uu.rounding
                FROM uom_uom uu
                WHERE (to_date(to_char(uu.write_date + INTERVAL '7 hours', 'dd-mm-yyyy'), 'dd-mm-yyyy') >= to_date(%s, 'dd-mm-yyyy') or %s = '')
                AND (to_date(to_char(uu.write_date + INTERVAL '7 hours', 'dd-mm-yyyy'), 'dd-mm-yyyy') <= to_date(%s, 'dd-mm-yyyy') or %s = '')
                    """
            from_date = Configs._validate_params(from_date)
            to_date = Configs._validate_params(to_date)
            cur.execute(query, (from_date, from_date, to_date, to_date))

            data = cur.fetchall()
            total_record = len(data)

            def __get_data():
                for line in data:
                    yield {
                        'name': line[0],
                        'id': line[1],
                        'active': line[2],
                        'rounding': line[3],
                    }

            cur.close()
            try:
                mesg = _('Get data successfully!')
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "total_record": total_record,
                                            "detail_data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '504', e)
                return Response.error(str(e), data={}).to_json()

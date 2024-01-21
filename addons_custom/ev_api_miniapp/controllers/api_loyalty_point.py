# -*- coding: utf-8 -*-

import psycopg2
from odoo import http, _

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response


class ApiLoyaltyPoint(http.Controller):

    @http.route('/loyalty_point/partner', methods=['POST'], type='json', auth='public')
    def get_loyalty_point(self):
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/loyalty_point/partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/loyalty_point/partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/loyalty_point/partner', '', params, '401', mesg)
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

            if 'partner_phone' not in params:
                mesg = _("Missing partner's phone!")
                Configs._set_log_api(remote_ip, '/loyalty_point/partner', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()
            partner_phone = params['partner_phone']

            cur = conn.cursor()
            query = """
                SELECT value_float FROM ir_property 
                WHERE name ='loyalty_points' 
                AND res_id='res.partner,'||(SELECT id FROM res_partner WHERE phone = %s AND active = true LIMIT 1)::TEXT
                    """
            partner_phone = Configs._validate_params(partner_phone)
            cur.execute(query, [partner_phone])
            res = cur.fetchone()
            data = res[0] if res else 0

            cur.close()
            try:
                mesg = _('Get data successfully!')
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '200', mesg)
                return Response.success(mesg, data={'points': data}).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '504', e)
                return Response.error(str(e), data={}).to_json()

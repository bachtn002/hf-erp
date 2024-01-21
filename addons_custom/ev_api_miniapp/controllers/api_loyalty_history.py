# -*- coding: utf-8 -*-

import psycopg2
from odoo import http, _

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response
from datetime import datetime


class ApiLoyaltyHistory(http.Controller):

    @http.route('/loyalty_history/partner', methods=['POST'], type='json', auth='public')
    def get_loyalty_history(self):
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/loyalty_history/partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/loyalty_history/partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/loyalty_history/partner', '', params, '401', mesg)
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

            if 'phone' not in params:
                mesg = _("Missing partner's phone!")
                Configs._set_log_api(remote_ip, '/loyalty_history/partner', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()
            partner_phone = params['phone']

            from_date = params.get('from_date') or ''
            to_date = params.get('to_date') or ''

            cur = conn.cursor()
            query = """
                SELECT ph.points as points,
                        ph.type as type, 
                        ph.order_id as order_id, 
                        po.pos_reference as order_bill, 
                        po.note as note, 
                        ps.name as pos_shop, 
                        po.date_order + INTERVAL '7 hours' as date_order
                FROM customer_point_history ph JOIN pos_order po on ph.order_id = po.id
                LEFT JOIN pos_shop as ps on po.x_pos_shop_id = ps.id
                JOIN res_partner as rp on rp.id = ph.partner_id
                WHERE rp.phone = %s
                AND (to_date(to_char(po.date_order + INTERVAL '7 hours', 'dd-mm-yyyy'), 'dd-mm-yyyy') >= to_date(%s, 'dd-mm-yyyy') or %s = '')
                AND (to_date(to_char(po.date_order + INTERVAL '7 hours', 'dd-mm-yyyy'), 'dd-mm-yyyy') <= to_date(%s, 'dd-mm-yyyy') or %s = '')
                    """
            partner_phone = Configs._validate_params(partner_phone)
            from_date = Configs._validate_params(from_date)
            to_date = Configs._validate_params(to_date)
            para = [partner_phone, from_date, from_date, to_date, to_date]

            sort = params.get('sort') or 'order_id'
            query += " order by " + sort
            cur.execute(query, para)
            data = cur.fetchall()
            total_record = len(data)
            if 'offset' in params or 'limit' in params:
                offset = params.get('offset') or 0
                limit = params.get('limit') or 100
                data = data[offset:offset + limit]
                # query += " OFFSET %s LIMIT %s"
                # para.extend([offset, limit])

            def __get_data():
                for line in data:
                    yield {
                        'points': line[0],
                        'type': line[1],
                        'order_id': line[2],
                        'order_bill': line[3],
                        'note': line[4],
                        'pos_shop': line[5],
                        'date_order': line[6],
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

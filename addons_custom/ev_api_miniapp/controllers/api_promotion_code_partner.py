# -*- coding: utf-8 -*-

import psycopg2
from odoo import http, _

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response


class ApiPromotionCodePartner(http.Controller):

    @http.route('/promotion_code/partner', methods=['POST'], type='json', auth='public')
    def get_promotion_code_partner(self):
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '401', mesg)
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
                Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()
            partner_phone = params['partner_phone']
            state = params.get('state') or ''

            cur = conn.cursor()
            query = """
                SELECT pp.id, pp.name as promotion_id, 
                pp.id as pos_promotion_id, 
                ppl.state as state, 
                ppl.promotion_code as code,
                 ppl.phone as phone,
                 pv.date as start_date,
                 pv.expired_date as end_date,
                 pv.x_condition_apply as condition_apply
                FROM phone_promotion_list ppl
                JOIN promotion_voucher pv ON ppl.promotion_voucher_id = pv.id
                LEFT JOIN pos_promotion pp ON pv.promotion_id = pp.id
                WHERE (ppl.phone = %s)
                AND (pv.state = %s or %s = '')
                
            """
            partner_phone = Configs._validate_params(partner_phone)
            state = Configs._validate_params(state)
            para = [partner_phone, state, state]
            if 'promotion_code' in params and params['promotion_code']:
                query = """
                            select id, promotion_id, pos_promotion_id, state, code, phone, start_date, end_date, condition_apply
                            from (""" + query + """
                            UNION
                            (select pp.id, pp.name as promotion_id,
                                   pp.id as pos_promotion_id,
                                   pvl.state_promotion_code as state,
                                   pvl.name as code,
                                   '' as phone,
                                   pv.date as start_date,
                                    pv.expired_date as end_date,
                                    pv.x_condition_apply as condition_apply
                                from promotion_voucher_line pvl
                            JOIN promotion_voucher pv ON pvl.promotion_voucher_id = pv.id
                            LEFT JOIN pos_promotion pp ON pv.promotion_id = pp.id
                            where pv.x_release_phone_types != 'phone'
                            and pvl.promotion_use_code = 1
                            AND (pv.state = %s or %s = ''))) a
                            where (a.code = %s or %s = '') 
                            """
                para_promotion_code = Configs._validate_params(params.get('promotion_code'))
                para.extend([state, state, para_promotion_code, para_promotion_code])

            sort = params.get('sort') or 'id'
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
                        'promotion_id': line[1],
                        'pos_promotion_id': line[2],
                        'state': line[3],
                        'code': line[4],
                        'phone': line[5],
                        'start_date': line[6],
                        'end_date': line[7],
                        'condition_apply': line[8],
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

# -*- coding: utf-8 -*-

import psycopg2
from odoo import http, _

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response


class ApiPosPromotion(http.Controller):

    @http.route('/pos_promotion', methods=['POST'], type='json', auth='public')
    def get_pos_promotion(self):
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/pos_promotion', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/pos_promotion', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/pos_promotion', '', params, '401', mesg)
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

            state = params.get('state') or ''
            channel_code = params.get('channel_code') or ''
            from_date = params.get('from_date') or ''
            to_date = params.get('to_date') or ''

            cur = conn.cursor()
            query = """
                SELECT pp.id,
                    pp.name,
                    pp.type,
                    pt.name promotion_type_id,
                    pp.priority,
                    CAST(pp.check_promotion as INT) as is_promotion_code,
                    pp.x_promotion_code_type as promotion_code_type, 
                    CAST(pp.x_allow_apply_with_other as INT) allow_apply_with_other,
                    
                    pp.start_date,
                    pp.end_date,
                    CAST(pp.time_add as INT),
                    pp.start_time,
                    pp.end_time,
                    CAST(pp.weekday_add as INT),
                    pp.state,
                    CAST(pp.apply_all_pos_config as INT)
                    
                FROM pos_promotion pp
                JOIN promotion_type pt ON pp.promotion_type_id = pt.id
                LEFT JOIN campaign_promotion cp ON pp.campaign_promotion = cp.id
                WHERE (pp.state = %s or %s = '')
                AND pp.type in ('qty_price', 'total_amount')
                AND (to_date(to_char(pp.write_date + INTERVAL '7 hours', 'dd-mm-yyyy'), 'dd-mm-yyyy') >= to_date(%s, 'dd-mm-yyyy') or %s = '')
                AND (to_date(to_char(pp.write_date + INTERVAL '7 hours', 'dd-mm-yyyy'), 'dd-mm-yyyy') <= to_date(%s, 'dd-mm-yyyy') or %s = '')
                AND (pp.id in (SELECT pp.id
                                FROM pos_promotion pp
                                JOIN pos_channel_pos_promotion_rel ppr
                                ON pp.id = ppr.pos_promotion_id
                                JOIN pos_channel pc on ppr.pos_channel_id = pc.id 
                                WHERE pc.code = %s) or %s = '')
            """
            state = Configs._validate_params(state)
            from_date = Configs._validate_params(from_date)
            to_date = Configs._validate_params(to_date)
            channel_code = Configs._validate_params(channel_code)
            para = [state, state, from_date, from_date, to_date, to_date, channel_code, channel_code]

            sort = params.get('sort') or 'id'
            query += " order by " + sort
            cur.execute(query, para)
            data = cur.fetchall()
            promotion_ids = []
            total_record = len(data)
            if 'offset' in params or 'limit' in params:
                offset = params.get('offset') or 0
                limit = params.get('limit') or 100
                data = data[offset:offset + limit]
                # query += " OFFSET %s LIMIT %s"
                # para.extend([offset, limit])
            for line in data:
                promotion_ids.append(line[0])
            promotion_ids = ','.join([str(id) for id in promotion_ids])

            channel_ids = self.get_channel(cur, promotion_ids)
            apply_pos_config_ids, apply_pos_in_state = self.get_apply_pos_config(cur, promotion_ids)
            weekdays = self._get_custom_weekdays(cur, promotion_ids)
            promotion_qty_price = self._get_qty_price(cur, promotion_ids)
            promotion_total_amount = self._get_total_amount(cur, promotion_ids)

            def __get_data():
                for line in data:
                    yield {
                        'id': line[0],
                        'name': line[1],
                        'type': line[2],
                        'promotion_type_id': line[3],
                        'priority': line[4],
                        'is_promotion_code': line[5],
                        'promotion_code_type': line[6],
                        'allow_apply_with_other': line[7],
                        'pos_channel_ids': channel_ids.get(line[0]) or [],
                        'start_date': line[8],
                        'end_date': line[9],
                        'apply_pos_config': apply_pos_config_ids.get(line[0]) if not line[15] else [],
                        'time_add': [{'start_time': '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line[11]) * 60, 60)),
                                      'end_time': '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line[12]) * 60, 60))
                                      }] if line[10] else [],
                        'weekday_add': weekdays.get(line[0]) if line[13] else [],
                        'apply_pos_in_states': apply_pos_in_state.get(line[0]) if not line[15] else [],
                        'state': line[14],
                        'pos_promotion_qty_price_apply_condition': promotion_qty_price.get(line[0]) or [],
                        'pos_promotion_total_amount_apply_condition': promotion_total_amount.get(line[0]) or []
                    }

            cur.close()
            try:
                mesg = _('Get data successfully!')
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "record_total": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, api_id.code, api_id.name,
                                     params, '504', e)
                return Response.error(str(e), data={}).to_json()

    def get_channel(self, cur, promotion_ids):
        dic = {}
        if len(promotion_ids) > 0:
            query = """
                SELECT pp.id, pc.code, pc.name
                FROM pos_promotion pp
                JOIN pos_channel_pos_promotion_rel ppr
                ON pp.id = ppr.pos_promotion_id
                JOIN pos_channel pc on ppr.pos_channel_id = pc.id
                WHERE pp.id = ANY (string_to_array(%s, ',')::integer[])
            """

            cur.execute(query, [promotion_ids])
            data = cur.fetchall()
            for channel in data:
                if channel[0] in dic.keys():
                    dic[channel[0]].append({'channel_code': channel[1], 'channel_name': channel[2]})
                else:
                    dic[channel[0]] = [{'channel_code': channel[1], 'channel_name': channel[2]}]
        return dic

    def get_apply_pos_config(self, cur, promotion_ids):
        dict_pos_shop = {}
        dict_state = {}
        if len(promotion_ids) > 0:
            query = """
                SELECT pp.id, pc.x_code_shop, pc.name, rcs.code, rcs.name
                FROM pos_promotion pp
                JOIN pos_config_pos_promotion_rel ppr
                ON pp.id = ppr.pos_promotion_id
                JOIN pos_config pc ON ppr.pos_config_id = pc.id
                JOIN pos_shop ps ON ps.id = pc.x_pos_shop_id
                LEFT JOIN res_country_state rcs ON rcs.id = ps.country_state_id
                WHERE pp.id = ANY (string_to_array(%s, ',')::integer[])
            """

            cur.execute(query, [promotion_ids])
            data = cur.fetchall()
            for pos in data:
                if pos[0] in dict_pos_shop.keys():
                    dict_pos_shop[pos[0]].append({'shop_code': pos[1], 'shop_name': pos[2]})
                else:
                    dict_pos_shop[pos[0]] = [{'shop_code': pos[1], 'shop_name': pos[2]}]

                if pos[3]:
                    if pos[0] in dict_state.keys():
                        if {'code_state': pos[3], 'name': pos[4]} not in dict_state[pos[0]]:
                            dict_state[pos[0]].append({'code_state': pos[3], 'name': pos[4]})
                    else:
                        dict_state[pos[0]] = [{'code_state': pos[3], 'name': pos[4]}]
        return dict_pos_shop, dict_state

    def _get_custom_weekdays(self, cur, promotion_ids):
        res = {}
        if len(promotion_ids) > 0:
            query = """
                SELECT pp.id, cw.name
                FROM pos_promotion pp
                JOIN custom_weekdays_pos_promotion_rel cwppr
                ON pp.id = cwppr.pos_promotion_id
                JOIN custom_weekdays cw ON cw.id = cwppr.custom_weekdays_id
                WHERE pp.id = ANY (string_to_array(%s, ',')::integer[])
                ORDER BY pp.id, cw.name
            """
            cur.execute(query, [promotion_ids])
            datas = cur.fetchall()
            for data in datas:
                if data[0] in res.keys():
                    res[data[0]].append(data[1])
                else:
                    res[data[0]] = [data[1]]
        return res

    def _get_qty_price(self, cur, promotion_ids):
        # Giá bán theo số lượng mua
        dic = {}
        if len(promotion_ids) > 0:
            query = """
                   SELECT ppqp.promotion_id, pp.id, pt.name, pp.default_code, ppqp.qty, 
                       ppqp.check_discount_price, ppqp.price_unit, ppqp.discount, ppqp.note
                   FROM pos_promotion_qty_price ppqp
                   JOIN product_product pp ON ppqp.product_id = pp.id
                    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    WHERE ppqp.promotion_id = ANY (string_to_array(%s, ',')::integer[])
                           """
            cur.execute(query, [promotion_ids])
            data = cur.fetchall()
            for promotion in data:
                if promotion[0] in dic.keys():
                    dic[promotion[0]].append({'product_id': promotion[1],
                                              'product_name': promotion[2],
                                              'default_code': promotion[3],
                                              'qty': promotion[4],
                                              'check_discount_price': promotion[5],
                                              'price_unit': promotion[6],
                                              'discount': promotion[7],
                                              'note': promotion[8],
                                              })
                else:
                    dic[promotion[0]] = [{'product_id': promotion[1],
                                          'product_name': promotion[2],
                                          'default_code': promotion[3],
                                          'qty': promotion[4],
                                          'check_discount_price': promotion[5],
                                          'price_unit': promotion[6],
                                          'discount': promotion[7],
                                          'note': promotion[8],
                                          }]
        return dic

    def _get_total_amount(self, cur, promotion_ids):
        # Giảm giá theo tổng giá trị đơn hàng
        dic = {}
        if len(promotion_ids) > 0:
            query = """
                SELECT promotion_id, total_amount, check_discount_price, 
                    price_discount, discount, max_discount
                FROM pos_promotion_total_amount
                WHERE promotion_id = ANY (string_to_array(%s, ',')::integer[])
            """
            cur.execute(query, [promotion_ids])
            data = cur.fetchall()
            for promotion in data:
                if promotion[0] in dic.keys():
                    dic[promotion[0]].append({'total_amount': promotion[1],
                                              'check_discount_price': promotion[2],
                                              'price_discount': promotion[3],
                                              'discount': promotion[4],
                                              'max_discount': promotion[5]
                                              })
                else:
                    dic[promotion[0]] = [{'total_amount': promotion[1],
                                          'check_discount_price': promotion[2],
                                          'price_discount': promotion[3],
                                          'discount': promotion[4],
                                          'max_discount': promotion[5]
                                          }]
        return dic

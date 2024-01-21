# -*- coding: utf-8 -*-
import psycopg2
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import http, _
from odoo.http import Controller, route

from ..helpers import Configs
from ..helpers.Response import Response


class PosOrderControllers(Controller):

    @route('/pos_payment', methods=['POST'], auth='public', type='json')
    def get_pos_payment(self):
        params = http.request.params
        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/pos_payment', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        # Check connection and token to make valid connection
        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/pos_payment', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()

        from_date = datetime.strptime(http.request.params.get('from_date'), '%d-%m-%Y').date()
        to_date = datetime.strptime(http.request.params.get('to_date'), '%d-%m-%Y').date()

        max_date = http.request.env['ir.config_parameter'].sudo().get_param('max_date_api')

        if from_date + relativedelta(days=int(max_date)) < to_date:
            to_date = from_date + relativedelta(days=int(max_date))

        from_date = datetime.strftime(from_date, '%Y-%m-%d')
        to_date = datetime.strftime(to_date, '%Y-%m-%d')

        global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date), str(to_date),
                                                                                    http.request.env.user)
        shop = 0
        if 'shop' in params:
            shop_code = params.get('shop')
            shop_id = http.request.env['pos.shop'].sudo().search([('code', '=', shop_code)], limit=1)
            shop = shop_id.id if shop_id else 0

        # get shop
        # if not shop_id or not shop_code:
        #     mesg = _("There is no shop matching with code %s") % shop_code
        #     Configs._set_log_api(remote_ip, '/pos_payment', '', params, '400', mesg)
        #     return Response.error(mesg, data={}, code='400').to_json()

        api_config = Configs._get_api_config(params['token_connect_api'])
        if not api_config:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/pos_payment', '', params, '401', mesg)
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
                    Configs._set_log_api(remote_ip, '/pos_payment', api_config.name, params, '400', str(e))
                    return Response.error(e, data={}).to_json()
            elif not check_connect and not api_config.preventive:
                return Response.error().to_json()
            # create a cursor
            cur = conn.cursor()
            # Execute a sql
            query = """
                            SELECT 
                                   ''                                   stt_rec,
                                   ''                                   so_ct,
                                   to_char(a.payment_date + INTERVAL '7 hours', 'dd-mm-yyyy')
                                                                        ngay_ct,
                                   d.name                               dien_giai,
                                   c.code                               ma_kh,
                                   g.code                               tk,
                                   '1311'                               tk_du,
                                   sum(a.amount)             as tien,
                                   ''                                   ong_ba
                            from pos_payment a
                                     join pos_shop c on c.id = a.x_pos_shop_id
                                     join pos_payment_method d on d.id = a.payment_method_id
                                     join account_journal f on f.id = d.cash_journal_id
                                     join account_account g on g.id = f.default_account_id
                            where (c.id = %s or %s = 0)
                                  and a.payment_date >= %s
                                  and a.payment_date <= %s
                            group by ngay_ct, d.id, c.id, c.code, g.code
                              """
            cur.execute(query, (shop, shop, global_from_date, global_to_date))

            payments = cur.fetchall()
            total_record = len(payments)
            def __get_data():
                for payment in payments:
                    yield {
                        "stt_rec": payment[0],
                        "so_ct": payment[1] or '',
                        "ngay_ct": payment[2],
                        "dien_giai": payment[3] or '',
                        "ma_kh": payment[4] or '',
                        "tk": payment[5] or '',
                        "tk_du": payment[6] or '',
                        "tien": payment[7],
                        "ong_ba": payment[8] or ''
                    }

            # close the communication with the PostgreSQL
            cur.close()
            try:
                mesg = _('Get data successfully!')
                Configs._set_log_api(remote_ip, '/pos_payment', api_config.name, params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "total_record": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, '/pos_payment', api_config.name, params, '400', str(e))
                return Response.error(str(e), data={}).to_json()

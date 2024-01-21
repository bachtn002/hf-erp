# -*- coding: utf-8 -*-
import psycopg2
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo import http, _
from odoo.http import Controller, route

from ..helpers import Configs
from ..helpers.Response import Response
from odoo.http import request


class PosOrderControllers(Controller):

    @route('/pos_order', methods=['POST'], auth='public', type='json')
    def get_pos_order(self):
        # Check connection and token to make valid connection
        params = http.request.params
        remote_ip = Configs.get_request_ip()
        # Check IP access in whitelist
        is_ip_valid = Configs.check_allow_ip(remote_ip)
        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/pos_order', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/pos_order', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        # bắt buộc truyền date
        if ('from_date' not in params and 'to_date' not in params) and (
                'from_invoice_date' not in params and 'to_invoice_date' not in params):
            mesg = _("Invalid parameter 'date'!")
            Configs._set_log_api(remote_ip, '/pos_order', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()
        if 'from_date' in params and 'from_invoice_date' in params:
            if not params['from_date'] and not params['from_invoice_date']:
                mesg = _("Invalid parameter 'date'!")
                Configs._set_log_api(remote_ip, '/pos_order', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()


        global_from_date = global_to_date = None
        global_from_invoice_date = global_to_invoice_date = None
        if 'from_date' in params and 'to_date' in params:
            if params['from_date'] and params['to_date']:
                from_date = datetime.strptime(params['from_date'], '%d-%m-%Y').date()
                to_date = datetime.strptime(params['to_date'], '%d-%m-%Y').date()
                max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')
                if from_date + relativedelta(days=int(max_date)) < to_date:
                    to_date = from_date + relativedelta(days=int(max_date))

                from_date = datetime.strftime(from_date, '%Y-%m-%d')
                to_date = datetime.strftime(to_date, '%Y-%m-%d')
                global_from_date, global_to_date = Configs.convert_from_date_to_date_global(str(from_date),
                                                                                            str(to_date),
                                                                                            http.request.env.user)
        if 'from_invoice_date' in params and 'to_invoice_date' in params:
            if params['from_invoice_date'] and params['to_invoice_date']:
                from_invoice_date = datetime.strptime(params['from_invoice_date'], '%d-%m-%Y').date()
                to_invoice_date = datetime.strptime(params['to_invoice_date'], '%d-%m-%Y').date()
                max_date = 0
                if 'from_date' not in params:
                    max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')
                elif not params['from_date']:
                    max_date = request.env['ir.config_parameter'].sudo().get_param('max_date_api')

                if from_invoice_date + relativedelta(days=int(max_date)) < to_invoice_date:
                    to_invoice_date = from_invoice_date + relativedelta(days=int(max_date))

                from_invoice_date = datetime.strftime(from_invoice_date, '%Y-%m-%d')
                to_invoice_date = datetime.strftime(to_invoice_date, '%Y-%m-%d')
                global_from_invoice_date, global_to_invoice_date = Configs.convert_from_date_to_date_global(
                    str(from_invoice_date), str(to_invoice_date),
                    http.request.env.user)

        get_invoice_issued = ('released', 'cancel_release')
        if 'get_invoice_issued' not in params or params['get_invoice_issued'] == 0 or params[
            'get_invoice_issued'] == None:
            get_invoice_issued = ('0', '0')
        if 'get_invoice_issued' in params and params['get_invoice_issued'] not in (0, 1):
            mesg = _("Invalid parameter 'get_invoice_issued'!")
            Configs._set_log_api(remote_ip, '/pos_order', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        shop = 0
        if 'shop' in params:
            shop_code = params.get('shop')
            shop_id = http.request.env['pos.shop'].sudo().search([('code', '=', shop_code)], limit=1)
            shop = shop_id.id if shop_id else 0

        api_config = Configs._get_api_config(params['token_connect_api'])
        if not api_config:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/pos_order', '', params, '401', mesg)
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
                    Configs._set_log_api(remote_ip, '/pos_order', api_config.name, params, '504', str(e))
                    return Response.error(e, data={}).to_json()
            elif not check_connect and not api_config.preventive:
                mesg = "An error occurred, please try again later"
                Configs._set_log_api(remote_ip, '/pos_order', api_config.name, params, '400', mesg)
                return Response.error().to_json()
            # create a cursor
            cur = conn.cursor()
            # Execute a sql
            query = """
                SELECT a.id as stt_rec,
                       b.pos_reference                                 so_ct,
                       to_char(b.date_order + INTERVAL '7 hours', 'dd/mm/yyyy')             ngay_ct,
                       e.name                                          dien_giai,
                       c.code                                          ma_kh,
                       d.default_code                                  ma_vt,
                       a.qty                                           so_luong,
                       a.price_unit                                    don_gia,
                       case
                           when a.qty >= 0 then
                           (a.price_subtotal_incl - a.x_is_price_promotion - a.amount_promotion_loyalty - a.amount_promotion_total) 
                           else 
                           (a.price_subtotal_incl + a.x_is_price_promotion + a.amount_promotion_loyalty + a.amount_promotion_total) 
                           end                                         as tien,
                       g.amount                                        ma_thue,
                       h.name                                          ong_ba,
                       case
                           when a.price_unit < 0 or a.discount = 100 then 1
                           else 0 end                               as km,
                       '0'                                             loai_tt,
                       b.sinvoice_vat          as                               masothue_invoice,
                       b.sinvoice_company_name as                               tencongty_invoice,
                       b.sinvoice_address      as                               diachi_invoice,
                       b.sinvoice_email        as                               email_invoice,
                       b.sinvoice_no           as                               hoadondientu,
                       b.sinvoice_series       as                               kyhieu_invoice,
                       b.sinvoice_issued_date + INTERVAL '7 hours' as           ngay_invoice,
                       b.sinvoice_state        as                               trangthai_invoice,
                       a.sinvoice_tax_amount   as                               thue_invoice
                from pos_order_line a
                         left join pos_order b on b.id = a.order_id
                         left join pos_shop c on c.id = b.x_pos_shop_id
                         left join product_product d on d.id = a.product_id
                         left join product_template e on e.id = d.product_tmpl_id
                         left join account_tax_pos_order_line_rel f on f.pos_order_line_id = a.id
                         left join account_tax g on g.id = f.account_tax_id
                         left join res_partner h on h.id = b.partner_id   
                where (c.id = %s or %s = 0)
                      and (b.sinvoice_state in %s or %s = ('0', '0'))
                      and a.price_unit >= 0
                      and not a.is_combo_line
                      --and b.x_pos_order_refund_id is null
                """
            if global_from_date and global_to_date and global_from_invoice_date and global_to_invoice_date:
                query += """
                      and b.date_order >= %s
                      and b.date_order <= %s
                      and b.sinvoice_issued_date >= %s
                      and b.sinvoice_issued_date <= %s
                    """
                params_sql = (
                    shop, shop,
                    get_invoice_issued, get_invoice_issued,
                    global_from_date, global_to_date,
                    global_from_invoice_date, global_to_invoice_date,
                )
            elif global_from_date and global_to_date:
                query += """
                      and b.date_order >= %s
                      and b.date_order <= %s
                """
                params_sql = (
                    shop, shop,
                    get_invoice_issued, get_invoice_issued,
                    global_from_date, global_to_date,
                )
            elif global_from_invoice_date and global_to_invoice_date:
                query += """
                      and b.sinvoice_issued_date >= %s
                      and b.sinvoice_issued_date <= %s
                """
                params_sql = (
                    shop, shop,
                    get_invoice_issued, get_invoice_issued,
                    global_from_invoice_date, global_to_invoice_date,
                )
            else:
                mesg = _("Some params passing invalid'!")
                Configs._set_log_api(remote_ip, '/pos_order', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()

            cur.execute(query, params_sql)


            pos_orders = cur.fetchall()
            total_record = len(pos_orders)

            def __get_data():
                for order in pos_orders:
                    if order[20] == 'no_release':
                        state_invoice = 'Chưa phát hành'
                    elif order[20] == 'released':
                        state_invoice = 'Đã phát hành'
                    elif order[20] == 'queue':
                        state_invoice = 'Trong hàng đợi'
                    elif order[20] == 'cancel_release':
                        state_invoice = 'Hủy phát hành'
                    else:
                        state_invoice = ''
                    yield {
                        "stt_rec": order[0],
                        "so_ct": order[1] or '',
                        "ngay_ct": order[2],
                        "dien_giai": order[3] or '',
                        "ma_kh": order[4] or '',
                        "ma_vt": order[5] or '',
                        "so_luong": order[6],
                        "don_gia": order[7],
                        "tien": order[8] if order[8] and order[8] >= 0 else 0.0,
                        "ma_thue": order[9] or 0.0,
                        "ong_ba": order[10] or '',
                        "km": order[11],
                        "loai_tt": order[12],
                        "masothue_invoice": order[13] or '',
                        "tencongty_invoice": order[14] or '',
                        "diachi_invoice": order[15] or '',
                        "email_invoice": order[16] or '',
                        "hoadondientu": order[17] or '',
                        "kyhieu_invoice": order[18] or '',
                        "ngay_invoice": order[19] or '',
                        "trangthai_invoice": state_invoice,
                        "thue_invoice": order[21] or 0.0,
                    }

            # close the communication with the PostgreSQL
            cur.close()
            try:
                mesg = _("Get data successfully!")
                Configs._set_log_api(remote_ip, '/pos_order', api_config.name, params, '200', mesg)
                return Response.success(mesg,
                                        data={
                                            "record_total": total_record,
                                            "data": list(__get_data()),
                                        }).to_json()
            except Exception as e:
                Configs._set_log_api(remote_ip, '/pos_order', api_config.name, params, '504', str(e))
                return Response.error(str(e), data={}).to_json()

    @route('/pos_order/cancel_sinvoice', methods=['POST'], auth='public', type='json')
    def get_pos_order_cancel_sinvoice(self):
        params = http.request.params
        remote_ip = Configs.get_request_ip()

        is_ip_valid = Configs.check_allow_ip(remote_ip)
        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        api_config = Configs._get_api_config(params['token_connect_api'])
        if not params.get('from_date') or 'from_date' not in params:
            mesg = _("Invalid parameter 'from_date'!")
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if not params.get('to_date') or 'to_date' not in params:
            mesg = _("Invalid parameter 'to_date'!")
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

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

        if not api_config:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', '', params, '401', mesg)
            return Response.error(mesg, data={}, code='401').to_json()
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
                Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', api_config.name, params, '504', str(e))
                return Response.error(e, data={}).to_json()
        elif not check_connect and not api_config.preventive:
            mesg = "An error occurred, please try again later"
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', api_config.name, params, '400', mesg)
            return Response.error().to_json()
        query = """
            SELECT a.id                    as                               stt_rec,
                   b.pos_reference                                          so_ct,
                   to_char(b.date_order + INTERVAL '7 hours', 'dd/mm/yyyy') ngay_ct,
                   e.name                                                   dien_giai,
                   c.code                                                   ma_kh,
                   d.default_code                                           ma_vt,
                   abs(a.qty)                                               so_luong,
                   a.price_unit                                             don_gia,
                   abs(case
                           when a.qty >= 0 then
                               (a.price_subtotal_incl - a.x_is_price_promotion - a.amount_promotion_loyalty -
                                a.amount_promotion_total)
                           else (case when a.price_subtotal_incl =0 then 0
                                       else (a.price_subtotal_incl + a.x_is_price_promotion + a.amount_promotion_loyalty +
                                                    a.amount_promotion_total) end)
                       end)                as                               tien,
                   g.amount                                                 ma_thue,
                   h.name                                                   ong_ba,
                   case
                       when a.price_unit < 0 or a.discount = 100 then 1
                       else 0 end          as                               km,
                   '0'                                                      loai_tt,
                   po.sinvoice_vat          as                               masothue_invoice,
                   po.sinvoice_company_name as                               tencongty_invoice,
                   po.sinvoice_address      as                               diachi_invoice,
                   po.sinvoice_email        as                               email_invoice,
                   po.sinvoice_no           as                               hoadondientu,
                   po.sinvoice_series       as                               kyhieu_invoice,
                   po.sinvoice_issued_date + INTERVAL '7 hours' as           ngay_invoice,
                   b.x_note_return        as                               ly_do_tra,
                   a.sinvoice_tax_amount    as                               thue_invoice
            from pos_order_line a
                     left join pos_order b on b.id = a.order_id
                     left join pos_shop c on c.id = b.x_pos_shop_id
                     left join product_product d on d.id = a.product_id
                     left join product_template e on e.id = d.product_tmpl_id
                     left join account_tax_pos_order_line_rel f on f.pos_order_line_id = a.id
                     left join account_tax g on g.id = f.account_tax_id
                     left join res_partner h on h.id = b.partner_id
                     join pos_order po on po.id = b.x_pos_order_refund_id
            where (c.id = %s or %s = 0)
              and b.date_order >= %s
              and b.date_order <= %s
              and po.sinvoice_state = 'cancel_release'
              and a.price_unit >= 0
              and b.x_pos_order_refund_id is not null
              and not a.is_combo_line;
        """
        cur = conn.cursor()
        cur.execute(query, (shop, shop, global_from_date, global_to_date))
        pos_orders = cur.fetchall()
        total_record = len(pos_orders)

        def __get_data():
            for order in pos_orders:
                yield {
                    "stt_rec": order[0],
                    "so_ct": order[1] or '',
                    "ngay_ct": order[2],
                    "dien_giai": order[3] or '',
                    "ma_kh": order[4] or '',
                    "ma_vt": order[5] or '',
                    "so_luong": order[6],
                    "don_gia": order[7],
                    "tien": order[8] if order[8] and order[8] >= 0 else 0.0,
                    "ma_thue": order[9] or 0.0,
                    "ong_ba": order[10] or '',
                    "km": order[11],
                    "loai_tt": order[12],
                    "masothue_invoice": order[13] or '',
                    "tencongty_invoice": order[14] or '',
                    "diachi_invoice": order[15] or '',
                    "email_invoice": order[16] or '',
                    "hoadondientu": order[17] or '',
                    "kyhieu_invoice": order[18] or '',
                    "ngay_invoice": order[19] or '',
                    "ly_do_tra": order[20] or '',
                    "thue_invoice": order[21] or 0.0,
                }

        cur.close()
        try:
            mesg = _("Get data successfully!")
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', api_config.name, params, '200', mesg)
            return Response.success(mesg,
                                    data={
                                        "record_total": total_record,
                                        "data": list(__get_data()),
                                    }).to_json()
        except Exception as e:
            Configs._set_log_api(remote_ip, '/pos_order/cancel_sinvoice', api_config.name, params, '504', str(e))
            return Response.error(str(e), data={}).to_json()

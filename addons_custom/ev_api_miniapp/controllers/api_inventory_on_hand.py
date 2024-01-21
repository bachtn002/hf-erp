# -*- coding: utf-8 -*-

import psycopg2
from odoo import http, _

from odoo.addons.ev_config_connect_api.helpers import Configs
from odoo.addons.ev_config_connect_api.helpers.Response import Response


class ApiInventoryOnhand(http.Controller):

    @http.route('/inventory/on_hand', methods=['POST'], type='json', auth='public')
    def get_inventory_on_hand(self):
        params = http.request.params

        remote_ip = Configs.get_request_ip()
        is_ip_valid = Configs.check_allow_ip(remote_ip)

        if not is_ip_valid:
            mesg = _("Your ip address is not allowed to access this API. Contact to your Admin!")
            Configs._set_log_api(remote_ip, '/inventory/on_hand', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        if 'token_connect_api' not in params:
            mesg = _("Missing token connection code!")
            Configs._set_log_api(remote_ip, '/inventory/on_hand', '', params, '400', mesg)
            return Response.error(mesg, data={}, code='400').to_json()

        token = params['token_connect_api']
        api_id = Configs._get_api_config(token)

        if not api_id:
            mesg = _("Token connection code no matching!")
            Configs._set_log_api(remote_ip, '/inventory/on_hand', '', params, '401', mesg)
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

            # if 'warehouse_code' not in params or params.get('warehouse_code') == "":
            #     mesg = _("Missing warehouse code!")
            #     Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '400', mesg)
            #     return Response.error(mesg, data={}, code='400').to_json()
            warehouse_code = ''
            if 'warehouse_code' in params:
                warehouse_code = params['warehouse_code']

            if 'product_code' not in params:
                mesg = _("Missing product_code params!")
                Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()
            product_code = params['product_code']

            if 'shop_code' not in params:
                mesg = _("Missing shop_code params!")
                Configs._set_log_api(remote_ip, '/promotion_code/partner', '', params, '400', mesg)
                return Response.error(mesg, data={}, code='400').to_json()
            shop_code = params['shop_code']

            cur = conn.cursor()
            query = """
              SELECT product_id, product_name, product_code, uom_id, sum(quantity), store_code
              FROM
                  (SELECT pp.id AS product_id,
                         pt.name AS product_name,
                         pt.default_code AS product_code,
                         uu.name AS uom_id,
                         - sum(pol.qty) AS quantity,
                         ps.code AS store_code
                  FROM pos_order_line pol
                      LEFT JOIN pos_order po ON po.id = pol.order_id
                      LEFT JOIN pos_shop ps ON ps.id = po.x_pos_shop_id
                      LEFT JOIN product_product pp ON pp.id = pol.product_id
                      LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                      LEFT JOIN uom_uom uu ON uu.id = pt.uom_id
                      JOIN stock_warehouse sw on ps.warehouse_id = sw.id
                      join pos_session pss ON pss.id = po.session_id
                  WHERE (sw.code = %s or %s = '')
                      AND (ps.code = %s OR %s = '')  
                      AND po.state = 'paid'
                      AND pt.active = True
                      AND pt.type = 'product'
                      AND pss.state != 'closed'
                      AND (pp.default_code = %s OR %s = '')
                  GROUP BY pp.id, pt.name, pt.default_code, uu.name, ps.code
                  UNION ALL
                  SELECT pt.id AS product_id,
                         pt.name AS product_name,
                         pt.default_code AS product_code,
                         uu.name AS uom_id,
                         ROUND(sq.quantity::numeric, 2) AS quantity,
                         ps.code AS store_code
                         --sw.code as store_code
                 FROM stock_warehouse sw
                      LEFT JOIN stock_quant sq ON sw.lot_stock_id = sq.location_id
                      JOIN product_product pp ON pp.id = sq.product_id
                      JOIN product_template pt ON pp.product_tmpl_id = pt.id
                      LEFT JOIN uom_uom uu ON pt.uom_id = uu.id
                      JOIN pos_shop ps ON ps.warehouse_id = sw.id
    
                  WHERE (sw.code = %s OR %s = '')
                      AND (pp.default_code = %s OR %s = '')
                      AND pt.active = True
                      AND pt.available_in_pos = True
                      AND (pt.id IN (SELECT psr.product_id FROM product_shop_rel psr JOIN pos_shop ps
                      ON psr.pos_shop_id = ps.id WHERE ps.code = %s AND ps.warehouse_id =  sw.id) OR %s = '')
                  ) AS sq
              GROUP BY product_id, product_name, product_code, uom_id, store_code
    
              """
            warehouse_code = Configs._validate_params(warehouse_code)
            product_code = Configs._validate_params(product_code)
            shop_code = Configs._validate_params(shop_code)
            para = [warehouse_code, warehouse_code, shop_code, shop_code, product_code, product_code,
                    warehouse_code, warehouse_code, product_code, product_code, shop_code, shop_code]

            sort = params.get('sort') or 'product_id'
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
                        'product_id': line[0],
                        'product_name': line[1],
                        'product_code': line[2],
                        'uom_id': line[3],
                        'quantity': line[4],
                        'store_code': line[5],
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

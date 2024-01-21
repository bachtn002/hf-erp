# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import ValidationError
import psycopg2


class StockDocumentStore(models.Model):
    _name = 'stock.document.store'
    _description = 'Bảng kê chi tiết nhập xuất'
    _auto = False

    def get_data(self, kwargs, state):
        rows = self._get_data_query(kwargs, state)
        total_quantity = 0
        for item in rows:
            total_quantity += item['sl'] if item['sl'] != '' else 0
        summary = {
            'total_quantity': total_quantity
        }
        return {
            'data': rows,
            'summary': summary
        }

    def _get_data_query(self, kwargs, state):
        date_from = kwargs.get('from_date').strftime('%d/%m/%Y')
        date_to = kwargs.get('to_date').strftime('%d/%m/%Y')
        location_ids = ','.join([str(i) for i in kwargs.get('location_ids')[0][2]]) if kwargs.get(
            'location_ids') else ''
        product_ids = ','.join([str(i) for i in kwargs.get('product_ids')[0][2]]) if kwargs.get(
            'product_ids') else ''
        x_all_internal = kwargs.get('x_all_internal')
        if x_all_internal:
            location_ids = ''
        try:
            host = self.env['ir.config_parameter'].sudo().get_param('slave_db_host')
            database = self.env['ir.config_parameter'].sudo().get_param('slave_db_name')
            user = self.env['ir.config_parameter'].sudo().get_param('slave_db_user')
            password = self.env['ir.config_parameter'].sudo().get_param('slave_db_password')
            port = self.env['ir.config_parameter'].sudo().get_param('slave_db_port')
            conn = psycopg2.connect(host=host, database=database, user=user, password=password,
                                    port=port)
            # create a cursor
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            sql_done = """
                SELECT 
                       --b.date                                             ngayy,
                       to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy') ngay,
                       COALESCE(bp.name, '')                              ten,
                       COALESCE(b.origin, '')                             mct,
                       COALESCE(b.x_description, '')                      lct,
                       COALESCE(CASE
                           WHEN bp.x_warehouse_out_name is null THEN COALESCE(('[' || d.name || ']' || d.name), d.name)
                           ELSE bp.x_warehouse_out_name
                           END, '') as                                         kho_xuat,
                       COALESCE(CASE
                           WHEN bp.x_warehouse_in_name is null THEN COALESCE(('[' || dd.name || ']' || dd.name), dd.name)
                           ELSE bp.x_warehouse_in_name
                           END, '')                                         kho_nhap,
                       COALESCE(rp.ref, '')                               marefkh,
                       COALESCE(rp.name, '')                              tenKH,
                       COALESCE(ct.default_code, '')                      masp,
                       COALESCE(ct.name, '')                              product_name,
                       COALESCE(e.name , '')                              lot_name,
                       COALESCE(u.name , '')                              dv,
                       COALESCE(sum(a.qty_done), 0)                       sl,
                       COALESCE(b.x_unit_cost , 0)                         dongia,
                       COALESCE(b.x_value , 0)                            giatri,
                       COALESCE(b.note, '')                               diengiai,
                       CASE
                           WHEN b.state = 'done' THEN 'Hoàn thành'
                           WHEN b.state = 'cancel' THEN 'Đã Hủy'
                           ELSE 'Chưa hoàn thành'
                           END as                                         state,
                        COALESCE(bp.note, '')                              note
        
                FROM stock_move b
                         LEFT JOIN stock_move_line a ON b.id = a.move_id
                         LEFT JOIN stock_picking bp ON b.picking_id = bp.id
                         LEFT JOIN res_partner rp ON rp.id = bp.partner_id
                         LEFT JOIN stock_picking_type spt ON spt.id = b.picking_type_id
                         LEFT JOIN product_product c ON c.id = b.product_id
                         LEFT JOIN product_template ct ON ct.id = c.product_tmpl_id
                         LEFT JOIN product_category cc ON cc.id = ct.categ_id
                         LEFT JOIN stock_location d ON d.id = a.location_id
                         LEFT JOIN stock_location dd ON dd.id = a.location_dest_id
                         LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                         LEFT JOIN uom_uom u ON b.product_uom = u.id
                WHERE to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
                  AND to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
                  AND b.state = 'done'
                  AND ((d.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '') or
                       (dd.id = ANY (string_to_array(%s, ',')::integer[]) or %s = ''))
                  AND (b.product_id = ANY (string_to_array(%s, ',')::integer[]) or %s = '')
                GROUP BY bp.x_warehouse_out_name, bp.x_warehouse_in_name, bp.note, bp.name, b.date, b.x_description, b.x_unit_cost,
                         b.x_value, d.name, d.name, dd.name, dd.name,
                         ct.default_code, ct.name, e.name, b.origin,
                         rp.name, b.note, b.state, u.name, rp.ref
                    """
            sql_no_done = """
                SELECT 
                       --b.date                                                ngayy,
                       to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy')    ngay,
                       COALESCE(bp.name, '')                                 ten,
                       COALESCE(b.origin, '')                                mct,
                       COALESCE(b.x_description, '')                         lct,
                       COALESCE(('[' || d.name || ']' || d.name), '')    kho_xuat,
                       COALESCE(('[' || dd.name || ']' || dd.name), '') kho_nhap,
                       COALESCE(rp.ref, '')                                  marefkh,
                       COALESCE(rp.name, '')                                 tenKH,
                       COALESCE(ct.default_code, '')                         masp,
                       COALESCE(ct.name, '')                                 product_name,
                       COALESCE(e.name , '')                                 lot_name,
                       COALESCE(u.name , '')                                 dv,
                       COALESCE(sum(a.qty_done), 0)                          sl,
                       COALESCE(b.x_unit_cost, 0)                             dongia,
                       COALESCE(b.x_value, 0)                                giatri,
                       COALESCE(b.note, '')                                  diengiai,
                       CASE
                           WHEN b.state = 'done' THEN 'Hoàn thành'
                           WHEN b.state = 'cancel' THEN 'Đã Hủy'
                           ELSE 'Chưa hoàn thành' END as                     state,
                        COALESCE(bp.note, '')                                 note
                FROM stock_move b
                         LEFT JOIN stock_move_line a ON b.id = a.move_id
                         LEFT JOIN stock_picking bp ON b.picking_id = bp.id
                         LEFT JOIN res_partner rp ON rp.id = bp.partner_id
                         LEFT JOIN stock_picking_type spt ON spt.id = b.picking_type_id
                         LEFT JOIN product_product c ON c.id = b.product_id
                         LEFT JOIN product_template ct ON ct.id = c.product_tmpl_id
                         LEFT JOIN product_category cc ON cc.id = ct.categ_id
                         LEFT JOIN stock_location d ON d.id = a.location_id
                         LEFT JOIN stock_location dd ON dd.id = a.location_dest_id
                         LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                         LEFT JOIN uom_uom u ON b.product_uom = u.id
                WHERE to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
                  AND to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
                  AND b.state != 'done'
                  AND ((d.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '') or
                       (dd.id = ANY (string_to_array(%s, ',')::integer[]) or %s = ''))
                  AND (b.product_id = ANY (string_to_array(%s, ',')::integer[]) or %s = '')
                GROUP BY bp.note, bp.name, b.date, b.x_description, b.x_unit_cost, b.x_value, d.name, d.name, dd.name, dd.name,
                         ct.default_code, ct.name, e.name, b.origin,
                         rp.name, b.note, b.state, u.name, rp.ref
            """
            params = (
                date_from, date_to, location_ids, location_ids, location_ids,
                location_ids, product_ids, product_ids)
            if state == 'done':
                sql = sql_done
            elif state == 'no_done':
                sql = sql_no_done
            else:
                sql = sql_done + 'UNION ALL' + sql_no_done
                params = (
                    date_from, date_to, location_ids, location_ids,
                    location_ids, location_ids, product_ids, product_ids,
                    date_from, date_to, location_ids, location_ids,
                    location_ids, location_ids, product_ids, product_ids
                )
            if not self.env.context.get('is_accountant'):
                sql = """select ngay, ten, mct, lct, kho_xuat, kho_nhap, marefkh,
                tenkh, masp, product_name, lot_name, dv, sl, diengiai,
                state, note from (""" + sql + """) l1"""

            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)

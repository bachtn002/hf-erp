# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import ValidationError
import psycopg2

class StockTransferStore(models.Model):
    _name = 'stock.transfer.store'
    _description = 'Stock Transfer Report'
    _auto = False

    def _get_data_query(self, kwargs):
        date_from = kwargs.get('from_date').strftime('%d/%m/%Y')
        date_to = kwargs.get('to_date').strftime('%d/%m/%Y') if kwargs.get('to_date') else date_from
        warehouse_ids = ','.join([str(i) for i in kwargs.get('warehouse_ids')[0][2]]) if kwargs.get(
            'warehouse_ids') else ''
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
            sql = """
                select st.name                            name_st,
                       swi.name                           warehouse_id,
                       swdi.name                          warehouse_dest_id,
                       pp.default_code                    default_code,
                       pt.name                            product_name,
                       uom.name                           uom,
                       stl.out_quantity                   out_quantity,
                       to_char(st.out_date, 'dd/mm/yyyy') out_date,
                       rp.name                            name_partner
                from stock_transfer st
                         left join stock_transfer_line stl on st.id = stl.stock_transfer_id
                         left join stock_warehouse swi on st.warehouse_id = swi.id
                         left join stock_warehouse swdi on st.warehouse_dest_id = swdi.id
                         left join uom_uom uom on stl.product_uom = uom.id
                         left join product_product pp on stl.product_id = pp.id
                         left join product_template pt on pp.product_tmpl_id = pt.id
                         left join res_users ru on st.create_uid = ru.id
                         left join res_partner rp on ru.partner_id = rp.id
                where st.state = 'transfer'
                  AND stl.out_quantity > 0
                  AND (swdi.id = ANY (string_to_array(%s, ',')::integer[]) OR %s = '')
                  AND to_date(to_char(st.out_date, 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
                  AND to_date(to_char(st.out_date, 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
                order by st.out_date
                    """
            params = (warehouse_ids, warehouse_ids, date_from, date_to)
            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)

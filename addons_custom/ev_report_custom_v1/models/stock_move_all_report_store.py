from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import psycopg2

class StockMoveAllReportStore(models.Model):
    _name = 'stock.move.all.report.store'
    _description = 'Stock Move All Report Store'
    _auto = False

    def get_data(self, **kwargs):
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')

        product_ids = kwargs.get('product_ids')
        company_id = kwargs.get('company_id')
        categ_ids = kwargs.get('categ_ids')

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
            SELECT * FROM
        (SELECT product_code, product_name, dv,
            SUM(tondau)-SUM(xuatkho)+SUM(nhapkho) sltoncuoi
        FROM (
        -- tồn kho đầu kỳ
                SELECT product_code, product_name, lot, hsd, dv, tracking,
                            SUM (nhapkho) - SUM (xuatkho) tondau, 
                            0 xuatkho, 
                            0 nhapkho
                FROM (
                        SELECT ('' || c.default_code || '') as product_code, pt.name product_name, e.name lot, 
                                to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
                                sum(a.qty_done) xuatkho, 0 nhapkho
                        FROM stock_move_line a
                        LEFT JOIN stock_move b ON b.id = a.move_id
                        LEFT JOIN product_product c ON c.id = a.product_id
                        LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                        LEFT JOIN stock_location d ON d.id = a.location_id
                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                        WHERE d.company_id = %s AND d.usage = 'internal'
                        AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND b.state = 'done'
                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(%s,'dd/mm/yyyy')
                        GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking
    
                        UNION ALL
    
                        SELECT ('' || c.default_code || '') as product_code, pt.name product_name, e.name lot, 
                                to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
                                0 xuatkho, sum(a.qty_done)nhapkho
                        FROM stock_move_line a
                        LEFT JOIN stock_move b ON b.id = a.move_id
                        LEFT JOIN product_product c ON c.id = a.product_id
                        LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                        LEFT JOIN stock_location d ON d.id = a.location_dest_id
                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                        WHERE d.company_id = %s AND d.usage = 'internal'
                        AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND b.state = 'done'
                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(%s,'dd/mm/yyyy')
                        GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking) as bang
                GROUP BY product_code, product_name, lot, hsd, dv, tracking
    
                UNION ALL
                -- xuất nhập kho trong kỳ
                SELECT product_code, product_name, lot, hsd, dv, tracking,
                            0 tondau, SUM(xuatkho) xuatkho, SUM(nhapkho) nhapkho
                FROM (
                        SELECT ('' || c.default_code || '') as product_code, pt.name product_name, e.name lot,
                                to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
                                sum(a.qty_done) xuatkho, 0 nhapkho
                        FROM stock_move_line a
                        LEFT JOIN stock_move b ON b.id = a.move_id
                        LEFT JOIN product_product c ON c.id = a.product_id
                        LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                        LEFT JOIN stock_location d ON d.id = a.location_id
                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                        WHERE d.company_id = %s AND d.usage = 'internal'
                        AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND b.state = 'done'
                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
                        GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking
                        
                        UNION ALL
                        
                        SELECT ('' || c.default_code || '') as product_code, pt.name product_name, e.name lot, 
                                to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
                                0 xuatkho, sum(a.qty_done)nhapkho
                        FROM stock_move_line a
                        LEFT JOIN stock_move b ON b.id = a.move_id
                        LEFT JOIN product_product c ON c.id = a.product_id
                        LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                        LEFT JOIN stock_location d ON d.id = a.location_dest_id
                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                        WHERE d.company_id = %s AND d.usage = 'internal'
                        AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                        AND b.state = 'done'
                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
                        GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking) as bang
                GROUP BY product_code, product_name, lot, hsd, dv, tracking) as bang_tong_hop
        GROUP BY product_code, product_name, dv, tracking
        ORDER BY product_name) as h
    WHERE (sltoncuoi != 0)
            """

            params = (company_id, categ_ids, categ_ids, product_ids, product_ids,
                      from_date, company_id, categ_ids, categ_ids, product_ids,
                      product_ids, from_date, company_id, product_ids,
                      categ_ids, categ_ids, product_ids, from_date, to_date,
                      company_id, categ_ids, categ_ids, product_ids, product_ids,
                      from_date, to_date)

            cur.execute(sql, params)
            result = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result
        except Exception as e:
            raise ValidationError(e)

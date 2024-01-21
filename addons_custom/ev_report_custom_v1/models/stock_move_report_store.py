from odoo import api, fields, models, _


class StockMoveReportStore(models.Model):
    _name = 'stock.move.report.store'
    _description = 'Stock Move Report Store'
    _auto = False

    def get_data(self, **kwargs):
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')

        location_ids = kwargs.get('location_ids')
        product_ids = kwargs.get('product_ids')
        company_id = kwargs.get('company_id')
        categ_ids = kwargs.get('categ_ids')

        sql = """
        SELECT * FROM
	(SELECT location_name, product_code, product_name, dv,
		SUM(tondau)-SUM(xuatkho)+SUM(nhapkho) sltoncuoi
	FROM (
	-- tồn kho đầu kỳ
			SELECT location_name, product_code, product_name, lot, hsd, dv, tracking,
						SUM (nhapkho) - SUM (xuatkho) tondau, 0 xuatkho, 0 nhapkho
			FROM (
					SELECT ('[' || d.name || ']' || d.name) as location_name, c.default_code product_code, pt.name product_name, e.name lot, 
							to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
							sum(a.qty_done) xuatkho, 0 nhapkho
					FROM stock_move_line a
					LEFT JOIN stock_move b ON b.id = a.move_id
					LEFT JOIN product_product c ON c.id = a.product_id
					LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
					LEFT JOIN stock_location d ON d.id = a.location_id
					LEFT JOIN stock_production_lot e ON e.id = a.lot_id
					LEFT JOIN uom_uom f ON f.id = a.product_uom_id
					WHERE (d.id = ANY(string_to_array(%s, ',')::integer[]) OR %s = '0')
					AND d.company_id = %s AND d.usage = 'internal'
					AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND b.state = 'done'
					AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(%s,'dd/mm/yyyy')
					GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking

					UNION ALL

					SELECT ('[' || d.name || ']' || d.name) as location_name, c.default_code product_code, pt.name product_name, e.name lot, 
						 	to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
						 	0 xuatkho, sum(a.qty_done)nhapkho
					FROM stock_move_line a
					LEFT JOIN stock_move b ON b.id = a.move_id
					LEFT JOIN product_product c ON c.id = a.product_id
					LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
					LEFT JOIN stock_location d ON d.id = a.location_dest_id
					LEFT JOIN stock_production_lot e ON e.id = a.lot_id
					LEFT JOIN uom_uom f ON f.id = a.product_uom_id
					WHERE (d.id = ANY(string_to_array(%s, ',')::integer[]) OR %s = '0')
					AND d.company_id = %s AND d.usage = 'internal'
					AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND b.state = 'done'
					AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(%s,'dd/mm/yyyy')
					GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking) as bang
			GROUP BY location_name, product_code, product_name, lot, hsd, dv, tracking

			UNION ALL
			-- xuất nhập kho trong kỳ
			SELECT location_name, product_code, product_name, lot, hsd, dv, tracking,
						0 tondau, SUM(xuatkho) xuatkho, SUM(nhapkho) nhapkho
			FROM (
					SELECT ('[' || d.name || ']' || d.name) as location_name, c.default_code product_code, pt.name product_name, e.name lot,
							to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
							sum(a.qty_done) xuatkho, 0 nhapkho
					FROM stock_move_line a
					LEFT JOIN stock_move b ON b.id = a.move_id
					LEFT JOIN product_product c ON c.id = a.product_id
					LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
					LEFT JOIN stock_location d ON d.id = a.location_id
					LEFT JOIN stock_production_lot e ON e.id = a.lot_id
					LEFT JOIN uom_uom f ON f.id = a.product_uom_id
					WHERE (d.id = ANY(string_to_array(%s, ',')::integer[]) OR %s = '0')
					AND d.company_id = %s AND d.usage = 'internal'
					AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND b.state = 'done'
					AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
					AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
					GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking
					
					UNION ALL
					
					SELECT ('[' || d.name || ']' || d.name) as location_name, c.default_code product_code, pt.name product_name, e.name lot, 
							to_char(e.expiration_date,'dd/mm/yyyy') hsd, f.name dv, pt.tracking, 
							0 xuatkho, sum(a.qty_done)nhapkho
					FROM stock_move_line a
					LEFT JOIN stock_move b ON b.id = a.move_id
					LEFT JOIN product_product c ON c.id = a.product_id
					LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
					LEFT JOIN stock_location d ON d.id = a.location_dest_id
					LEFT JOIN stock_production_lot e ON e.id = a.lot_id
					LEFT JOIN uom_uom f ON f.id = a.product_uom_id
					WHERE (d.id = ANY(string_to_array(%s, ',')::integer[]) OR %s = '0')
					AND d.company_id = %s AND d.usage = 'internal'
					AND (pt.categ_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND (b.product_id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
					AND b.state = 'done'
					AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
					AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
					GROUP BY d.name, d.company_id, c.default_code, pt.name, a.product_id, e.name, e.expiration_date, f.name, pt.tracking) as bang
			GROUP BY location_name, product_code, product_name, lot, hsd, dv, tracking) as bang_tong_hop
	GROUP BY location_name, product_code, product_name, dv, tracking
	ORDER BY location_name, product_name) as h
WHERE (sltoncuoi != 0)
        """

        params = (location_ids, location_ids, company_id, categ_ids, categ_ids,
                product_ids, product_ids, from_date, location_ids, location_ids,
                company_id, categ_ids, categ_ids, product_ids, product_ids,
                from_date, location_ids, location_ids, company_id, product_ids,
                categ_ids, categ_ids, product_ids, from_date, to_date,
                location_ids, location_ids, company_id, categ_ids, categ_ids,
                product_ids, product_ids, from_date, to_date)

        self._cr.execute(sql, params)
        return self._cr.dictfetchall()

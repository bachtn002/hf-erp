from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _generate_list_product_or_lot(self, product_ids, lot_ids, date_to, location_id):
        query = f'''SELECT product_id, product_name, lot_id, lot, SUM(nhapkho)-SUM(xuatkho) ton
                    FROM (
                        select c.id product_id, pt.name product_name,e.id lot_id, e.name lot, sum(a.qty_done) xuatkho, 0 nhapkho
                        from stock_move_line a
                        left join stock_move b ON b.id = a.move_id
                        left join product_product c ON c.id = a.product_id
                        left join product_template pt ON pt.id = c.product_tmpl_id
                        left join stock_location d ON d.id = a.location_id
                        left join stock_production_lot e ON e.id = a.lot_id
                        where d.id = {location_id}
                        and d.usage = 'internal'
                        and (CASE
                                    WHEN a.lot_id is not NULL THEN
                                            (a.lot_id = ANY(string_to_array('{lot_ids}', ',')::integer[]) or '{lot_ids}' = '0')
                                    ELSE
                                            (a.product_id = ANY(string_to_array('{product_ids}', ',')::integer[]) or '{product_ids}' = '0')
                                    END)
                        and b.state = 'done'
                        and to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date('{date_to}','dd/mm/yyyy')
                        group by c.id, pt.name, e.id, e.name
                        UNION ALL
                        select c.id product_id, pt.name product_name, e.id lot_id, e.name lot, 0 xuatkho, sum(a.qty_done) nhapkho
                        from stock_move_line a
                        left join stock_move b ON b.id = a.move_id
                        left join product_product c ON c.id = a.product_id
                        left join product_template pt ON pt.id = c.product_tmpl_id
                        left join stock_location d ON d.id = a.location_dest_id
                        left join stock_production_lot e ON e.id = a.lot_id
                        where d.id = {location_id}
                        and d.usage = 'internal'
                        and (CASE
                                    WHEN a.lot_id is not NULL THEN
                                            (a.lot_id = ANY(string_to_array('{lot_ids}', ',')::integer[]) or '{lot_ids}' = '0')
                                    ELSE
                                            (a.product_id = ANY(string_to_array('{product_ids}', ',')::integer[]) or '{product_ids}' = '0')
                                    END)
                        and b.state = 'done'
                        and to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date('{date_to}','dd/mm/yyyy')
                        group by c.id, pt.name, e.id, e.name) as bang
                    GROUP BY product_id, product_name, lot_id ,lot
                    ORDER BY lot_id'''
        self._cr.execute(query)
        return self._cr.fetchall()

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm


class StockConfigReport(models.Model):
    _name = 'stock.config.report'
    _order = "code asc"

    name = fields.Char('Name')
    code = fields.Char('Code', readonly=True)
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    description = fields.Text('Description')

    @api.model
    def create(self, values):
        result = super(StockConfigReport, self).create(values)
        from_date = result.from_date.strftime('%d/%m/%Y')
        to_date = result.to_date.strftime('%d/%m/%Y')
        str_from_date = result.from_date.strftime('%d_%m_%Y')
        str_to_date = result.to_date.strftime('%d_%m_%Y')
        result.code = 'materialized_stock_inventory_' + str_from_date + '_' + str_to_date
        if not result.name or result.name == '':
            result.name = _('Sumary stock inventory ') + from_date + ' - ' + to_date
        result._create_materialized(from_date, to_date)
        return result

    def _create_materialized(self, str_from_date, str_to_date):
        cr = self._cr
        query = "SELECT matviewname FROM pg_matviews WHERE matviewname = %s"
        cr.execute(query, (self.code,))
        result = cr.dictfetchall()
        if result:
            self._drop_materialized()
        create_query = """
        CREATE MATERIALIZED VIEW public.""" + self.code + """ AS
            (SELECT * FROM
                (SELECT location_code, location_name, product_code, product_name, lot, dv, tracking, dvm, 
                SUM(tondau) dauky, SUM(xuatkho) xuatkho, SUM(nhapkho) nhapkho, SUM(tondau) - SUM(xuatkho) + SUM(nhapkho) toncuoi,
                
                SUM(tondaudvm) daukydvm, SUM(xuatkhodvm) xuatkhodvm, SUM(nhapkhodvm) nhapkhodvm, SUM(tondaudvm) - SUM(xuatkhodvm) + SUM(nhapkhodvm) toncuoidvm
                FROM (
                -- tồn kho đầu kỳ
                        SELECT location_code, location_name, product_code, product_name, lot, dv, tracking, dvm,
                                    SUM (nhapkho) - SUM (xuatkho) tondau, 0 xuatkho, 0 nhapkho, 0 toncuoi,
                                    SUM (nhapkhodvm) - SUM (xuatkhodvm) tondaudvm, 0 xuatkhodvm, 0 nhapkhodvm, 0 toncuoidvm
                        FROM (
                                SELECT d.x_code as location_code, d.name as location_name, 	
                                        c.default_code product_code, pt.name product_name, e.name lot, g.name dv, pt.tracking, h.name dvm,
                                        sum(case when f.id = g.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/g.factor,5) end) xuatkho, 0 nhapkho,
                                        sum(case when f.id = h.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/h.factor,5) end) xuatkhodvm, 0 nhapkhodvm 
                                FROM stock_move_line a
                                LEFT JOIN stock_move b ON b.id = a.move_id
                                LEFT JOIN product_product c ON c.id = a.product_id
                                LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                                LEFT JOIN stock_location d ON d.id = a.location_id
                                LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                INNER JOIN uom_uom g on g.id = pt.uom_id
                                INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal'
                                AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(%s,'dd/mm/yyyy')
                                GROUP BY d.x_code, d.name, c.default_code, pt.name, e.name, g.name, pt.tracking, h.name
            
                                UNION ALL
            
                                SELECT d.x_code as location_code, d.name as location_name, 
                                        c.default_code product_code, pt.name product_name, e.name lot, g.name dv, pt.tracking, h.name dvm,
                                        0 xuatkho, sum(case when f.id = g.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/g.factor,5) end) nhapkho,   
                                        0 xuatkhodvm, sum(case when f.id = h.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/h.factor,5) end) nhapkhodvm
                                FROM stock_move_line a
                                LEFT JOIN stock_move b ON b.id = a.move_id
                                LEFT JOIN product_product c ON c.id = a.product_id
                                LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                                LEFT JOIN stock_location d ON d.id = a.location_dest_id
                                LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                INNER JOIN uom_uom g on g.id = pt.uom_id
                                INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal'
                                AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') < to_date(%s,'dd/mm/yyyy')
                                GROUP BY d.x_code, d.name, c.default_code, pt.name, e.name, g.name, pt.tracking, h.name) as bang
                        GROUP BY location_code, location_name, product_code, product_name, lot, dv, tracking, dvm
            
                        UNION ALL
                        -- xuất nhập kho trong kỳ
                        SELECT location_code, location_name, product_code, product_name, lot, dv, tracking, dvm, 
                                    0 tondau, SUM (xuatkho) xuatkho, SUM (nhapkho) nhapkho, 0 toncuoi,
                                    0 tondaudvm, SUM (xuatkhodvm) xuatkhodvm, SUM (nhapkhodvm) nhapkhodvm, 0 toncuoidvm
                        FROM (
                                SELECT d.x_code as location_code, d.name as location_name, 
                                        c.default_code product_code, pt.name product_name, e.name lot, g.name dv, pt.tracking, h.name dvm,
                                        sum(case when f.id = g.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/g.factor,5) end) xuatkho, 0 nhapkho,
                                        sum(case when f.id = h.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/h.factor,5) end) xuatkhodvm, 0 nhapkhodvm
                                FROM stock_move_line a
                                LEFT JOIN stock_move b ON b.id = a.move_id
                                LEFT JOIN product_product c ON c.id = a.product_id
                                LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                                LEFT JOIN stock_location d ON d.id = a.location_id
                                LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                INNER JOIN uom_uom g on g.id = pt.uom_id
                                INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal'
                                AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
                                AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
                                GROUP BY d.x_code, d.name, c.default_code, pt.name, e.name, g.name, pt.tracking, h.name
                                
                                UNION ALL
                                
                                SELECT d.x_code as location_code, d.name as location_name, 
                                        c.default_code product_code, pt.name product_name, e.name lot, g.name dv, pt.tracking, h.name dvm, 
                                        0 xuatkho, sum(case when f.id = g.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/g.factor,5) end) nhapkho,
                                        0 xuatkhodvm, sum(case when f.id = h.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/h.factor,5) end) nhapkhodvm
                                FROM stock_move_line a
                                LEFT JOIN stock_move b ON b.id = a.move_id
                                LEFT JOIN product_product c ON c.id = a.product_id
                                LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                                LEFT JOIN stock_location d ON d.id = a.location_dest_id
                                LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                INNER JOIN uom_uom g on g.id = pt.uom_id
                                INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal'
                                AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
                                AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
                                GROUP BY d.x_code, d.name, c.default_code, pt.name, e.name, g.name, pt.tracking, h.name) as bang
                        GROUP BY location_code, location_name, product_code, product_name, lot, dv, tracking, dvm) as bang_tong_hop
                GROUP BY location_code, location_name, product_code, product_name, lot, dv, tracking, dvm
                ORDER BY location_code, location_name, product_code) as h
            WHERE (xuatkho != 0 or nhapkho != 0 or toncuoi != 0))
        """
        self._cr.execute(create_query,(str_from_date, str_from_date, str_from_date, str_to_date, str_from_date, str_to_date,))

    def _drop_materialized(self):
        drop_query = "DROP MATERIALIZED VIEW " + self.code
        self._cr.execute(drop_query,)
        return True

    def refresh_materialized(self):
        refresh_query = "REFRESH MATERIALIZED VIEW " + self.code
        self._cr.execute(refresh_query,)
        return True

    def write(self, values):
        result = super(StockConfigReport, self).write(values)
        if 'from_date' in values or 'to_date' in values:
            self._drop_materialized()
            from_date = self.from_date.strftime('%d/%m/%Y')
            to_date = self.to_date.strftime('%d/%m/%Y')
            str_from_date = self.from_date.strftime('%d_%m_%Y')
            str_to_date = self.to_date.strftime('%d_%m_%Y')
            self.code = 'materialized_stock_inventory_' + str_from_date + '_' + str_to_date
            if not result.name or result.name == '':
                self.name = _('Sumary stock inventory ') + from_date + ' - ' + to_date
            self._create_materialized(from_date, to_date)
        return result

    def unlink(self):
        cr = self._cr
        query = "SELECT matviewname FROM pg_matviews WHERE matviewname = 'materialized_stock_move_multi'"
        cr.execute(query, )
        result = cr.dictfetchall()
        if result:
            drop_query = "DROP MATERIALIZED VIEW materialized_stock_move_multi"
            cr.execute(drop_query, )
        for order in self:
            order._drop_materialized()
        return super(StockConfigReport, self).unlink()
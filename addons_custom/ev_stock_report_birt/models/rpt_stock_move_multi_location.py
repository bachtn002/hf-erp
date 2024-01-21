# -*- coding: utf-8 -*-
import odoo.tools.config as config
from odoo import models, fields, api, exceptions


class RPTStockMoveMulti(models.TransientModel):
    _name = 'rpt.stock.move.multi'

    name = fields.Char(string='Inventory Report')
    location_ids = fields.Many2many('stock.location', string='Locations')
    category_ids = fields.Many2many('product.category', string='Product Categories')
    product_ids = fields.Many2many('product.product', string='Products')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    type = fields.Selection(
        [('inventory', 'Inventory report'), ('general', 'General account of input – output – inventory')],
        string='Report Type', default='inventory')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def _generate_data(self):
        config_id = self.env['stock.config.report'].search([('to_date', '<', self.from_date)], order='to_date desc',
                                                           limit=1)
        if not config_id:
            raise exceptions.ValidationError("No config stock inventory!")
        materialized_config = config_id.code
        to_date_config = config_id.to_date.strftime('%d/%m/%Y')
        from_date = self.from_date.strftime('%d/%m/%Y')
        to_date = self.to_date.strftime('%d/%m/%Y')
        company_id = self.company_id.id
        location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
        category_ids = ','.join([str(idd) for idd in self.category_ids.ids]) if self.category_ids else '0'
        product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
        cr = self._cr
        query = "SELECT matviewname FROM pg_matviews WHERE matviewname = 'materialized_stock_move_multi'"
        cr.execute(query, )
        result = cr.dictfetchall()
        if result:
            drop_query = "DROP MATERIALIZED VIEW materialized_stock_move_multi"
            cr.execute(drop_query, )
        create_query = """
                CREATE MATERIALIZED VIEW public.materialized_stock_move_multi AS
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
                                        SELECT a.location_code, a.location_name, a.product_code, a.product_name, a.lot, a.dv, a.tracking, h.name dvm,
                                              0 as xuatkho, sum(a.toncuoi) as nhapkho,0 as xuatkhodvm, sum(a.toncuoidvm) as nhapkhodvm
                                        FROM """ + materialized_config + """ AS a
                                        LEFT JOIN stock_location d ON d.x_code = a.location_code
                                        LEFT JOIN product_product c ON c.default_code = a.product_code
                                        LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                        LEFT JOIN uom_uom h on h.id = pt.uom_po_id
                                        WHERE d.company_id = %s
                                        AND (d.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (c.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (pc.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        GROUP BY a.location_code, a.location_name, a.product_code, a.product_name, a.lot, a.dv, a.tracking, h.name
                                        
                                        UNION ALL
                                        
                                        SELECT d.x_code as location_code, d.name as location_name, 	
                                                c.default_code product_code, pt.name product_name, e.name lot, g.name dv, pt.tracking, h.name dvm,
                                                sum(case when f.id = g.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/g.factor,5) end) xuatkho, 0 nhapkho,
                                                sum(case when f.id = h.id then a.qty_done else a.qty_done * round(1/f.factor,5) / round(1/h.factor,5) end) xuatkhodvm, 0 nhapkhodvm 
                                        FROM stock_move_line a
                                        LEFT JOIN stock_move b ON b.id = a.move_id
                                        LEFT JOIN product_product c ON c.id = a.product_id
                                        LEFT JOIN product_template pt ON pt.id = c.product_tmpl_id
                                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                        LEFT JOIN stock_location d ON d.id = a.location_id
                                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                        INNER JOIN uom_uom g on g.id = pt.uom_id
                                        INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                        WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal' and d.company_id = %s
                                        AND (d.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (c.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (pc.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') > to_date(%s,'dd/mm/yyyy')
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
                                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                        LEFT JOIN stock_location d ON d.id = a.location_dest_id
                                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                        INNER JOIN uom_uom g on g.id = pt.uom_id
                                        INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                        WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal' and d.company_id = %s
                                        AND (d.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (c.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (pc.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') > to_date(%s,'dd/mm/yyyy')
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
                                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                        LEFT JOIN stock_location d ON d.id = a.location_id
                                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                        INNER JOIN uom_uom g on g.id = pt.uom_id
                                        INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                        WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal' and d.company_id = %s
                                        AND (d.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (c.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (pc.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
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
                                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                                        LEFT JOIN stock_location d ON d.id = a.location_dest_id
                                        LEFT JOIN stock_production_lot e ON e.id = a.lot_id
                                        LEFT JOIN uom_uom f ON f.id = a.product_uom_id
                                        INNER JOIN uom_uom g on g.id = pt.uom_id
                                        INNER JOIN uom_uom h on h.id = pt.uom_po_id
                                        WHERE b.state = 'done' and c.active = 't' and d.usage = 'internal' and d.company_id = %s
                                        AND (d.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (c.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND (pc.id = ANY(string_to_array(%s, ',')::integer[]) or %s = '0')
                                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') >= to_date(%s,'dd/mm/yyyy')
                                        AND to_date(to_char(a.date + INTERVAL '7 hours','dd/mm/yyyy'),'dd/mm/yyyy') <= to_date(%s,'dd/mm/yyyy')
                                        GROUP BY d.x_code, d.name, c.default_code, pt.name, e.name, g.name, pt.tracking, h.name) as bang
                                GROUP BY location_code, location_name, product_code, product_name, lot, dv, tracking, dvm) as bang_tong_hop
                        GROUP BY location_code, location_name, product_code, product_name, lot, dv, tracking, dvm
                        ORDER BY location_code, location_name, product_code) as h
                    WHERE (xuatkho != 0 or nhapkho != 0 or toncuoi != 0))
                """
        cr.execute(create_query, (
            company_id, location_ids, location_ids, product_ids, product_ids, category_ids, category_ids,
            company_id, location_ids, location_ids, product_ids, product_ids, category_ids, category_ids,
            to_date_config, from_date,
            company_id, location_ids, location_ids, product_ids, product_ids, category_ids, category_ids,
            to_date_config, from_date,
            company_id, location_ids, location_ids, product_ids, product_ids, category_ids, category_ids, from_date,
            to_date,
            company_id, location_ids, location_ids, product_ids, product_ids, category_ids, category_ids, from_date,
            to_date))

    def action_export_report(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_to = self.to_date.strftime('%d/%m/%Y')
        if self.type == 'inventory':
            report_name = "rpt_stock_move_multi.rptdesign"
            self.from_date = self.to_date
        else:
            report_name = "rpt_stock_move_in_out_multi.rptdesign"
        date_from = self.from_date.strftime('%d/%m/%Y')
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&company_id': self.company_id.id,
        }
        birt_link = birt_url + report_name
        self._generate_data()
        return {
            "type": "ir.actions.client",
            'name': 'Multi Inventory Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }

    def action_report_excel(self):
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise exceptions.ValidationError("No config birt_url!")
        date_to = self.to_date.strftime('%d/%m/%Y')
        if self.type == 'inventory':
            report_name = "rpt_stock_move_multi.rptdesign"
            self.from_date = self.to_date
            date_from = self.to_date.strftime('%d/%m/%Y')
        else:
            report_name = "rpt_stock_move_in_out_multi.rptdesign"
            date_from = self.from_date.strftime('%d/%m/%Y')
        param_str = {
            '&from_date': date_from,
            '&to_date': date_to,
            '&company_id': self.company_id.id,
        }
        birt_link = birt_url + report_name
        self._generate_data()
        return {
            "type": "ir.actions.client",
            'name': 'Multi Inventory Report',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link + '&__format=xlsx',
                'payload_data': param_str,
            }
        }

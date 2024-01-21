# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo import tools


class StockInOutReport(models.TransientModel):
    _name = 'stock.in.out.report'
    _description = 'Stock In Out Report'

    location = fields.Char('Location Warehouse')
    default_code = fields.Char('Default Code')
    product = fields.Char('Product')
    uom = fields.Char('Uom')
    qty_begin = fields.Float('Quantity Begin', default=0, digits='Product Unit of Measure')
    qty_in = fields.Float('Quantity In', default=0, digits='Product Unit of Measure')
    qty_out = fields.Float('Quantity Out', default=0, digits='Product Unit of Measure')
    qty_end = fields.Float('Quantity End', default=0, digits='Product Unit of Measure')
    report_id = fields.Char('Report ID')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'v_stock_in_out_report')
        query = """
            CREATE OR REPLACE VIEW v_stock_in_out_report AS
            select b.name         as location,
                   c.default_code as default_code,
                   d.name         as product,
                   e.name         as uom,
                   a.qty_begin    as qty_begin,
                   a.qty_in       as qty_in,
                   a.qty_out      as qty_out,
                   a.qty_end      as qty_end,
                   a.location_id  as location_id,
                   a.product_id   as product_id,
                   d.categ_id     as categ_id,
                   a.month        as month,
                   a.year         as year,
                   a.date_sync         as date
            from stock_general_monthly a
                     join stock_location b on b.id = a.location_id
                     join product_product c on c.id = a.product_id
                     join product_template d on d.id = c.product_tmpl_id
                     join uom_uom e on e.id = d.uom_id
        """
        self.env.cr.execute(query)

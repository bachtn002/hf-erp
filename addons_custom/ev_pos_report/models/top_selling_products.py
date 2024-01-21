# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class ProductCategory(models.Model):
    _inherit = 'product.category'

    filter_report = fields.Boolean('Filter Report', default=False)


class TopSellingProducts(models.TransientModel):
    _name = 'top.selling.products.report'

    name = fields.Char(default='Báo cáo top sản phẩm bán chạy')
    from_date = fields.Date('From date', default=fields.Date.today())
    to_date = fields.Date('To date', default=fields.Date.today())
    lines = fields.One2many('top.selling.products.line', 'selling_product_id',
                            'Top Selling Products Line')
    limited = fields.Integer('Limited', default=0)
    product_category = fields.Many2one('product.category', domain="[('filter_report','=', True)]", string="Product Category")

    def action_report(self):
        self.update({
            'name': 'Báo cáo top sản phẩm bán chạy từ ngày ' + str(self.from_date) + ' đến ngày ' + str(self.to_date)
        })
        product_category_ids = [categ_id.id for categ_id in self.product_category if categ_id.id]
        if not product_category_ids:
            category_ids = self.env['product.category'].search([('filter_report','=', True)])
            product_category_ids = [categ_id.id for categ_id in category_ids if categ_id.id]

        if len(product_category_ids) == 1:
            product_category_ids.append(0)
            product_category_ids = tuple(product_category_ids)
        else:
            product_category_ids = tuple(product_category_ids)

        if self.limited <= 0:
            sql = """
                DELETE from top_selling_products_line where selling_product_id = %d;
                INSERT INTO top_selling_products_line(selling_product_id,product_categ_id,quantity,create_date, create_uid,write_uid,write_date)
                SELECT 
                    (%d) selling_product_id,
                    pt.categ_id product_categ_id,
                    sum(pol.qty) quantity,
                    now() create_date,
                    (%d) create_uid,
                    (%d) write_uid,
                    now() write_date
                FROM 
                    pos_order_line pol 
                    JOIN pos_order po ON (po.id = pol.order_id)
                    JOIN product_product pp ON (pol.product_id = pp.id)
                    JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                    JOIN product_category pct ON (pt.categ_id = pct.id)
                WHERE 
                    (po.date_order + INTERVAL '7 hours')::date >= '%s' AND 
                    (po.date_order + INTERVAL '7 hours')::date <= '%s' AND
                    po."state" in ('paid','done','invoiced') AND
                    pct.id in %s
                GROUP BY
                    product_categ_id
                ORDER BY
                    quantity DESC
            """
            self._cr.execute(sql % (self.id, self.id, self.env.user.id, self.env.user.id, self.from_date, self.to_date, product_category_ids))
        else:
            sql = """
                DELETE from top_selling_products_line where selling_product_id = %d;
                INSERT INTO top_selling_products_line(selling_product_id,product_categ_id,quantity,create_date, create_uid,write_uid,write_date)
                
                SELECT 
                 	(%d) selling_product_id,
                    pct.id product_categ_id,
                    sum(pol.qty) quantity,
                    now() create_date,
                 	(%d) create_uid,
                 	(%d) write_uid,
                    now() write_date
                FROM 
                    pos_order_line pol 
                    JOIN pos_order po ON (po.id = pol.order_id)
                    JOIN product_product pp ON (pol.product_id = pp.id)
                    JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                    JOIN product_category pct ON (pt.categ_id = pct.id)
                WHERE 
                    (po.date_order + INTERVAL '7 hours')::date >= '%s' AND 
                    (po.date_order + INTERVAL '7 hours')::date <= '%s' AND
                    po."state" in ('paid','done','invoiced') AND
                    pt.id in (
                        select product_code from (
                            SELECT 
                                (select pt.id from product_template pt,product_product pp where pt.id = pp.product_tmpl_id and pp.id = pol.product_id) product_code,
                                sum(pol.qty) qty
                            FROM 
                                pos_order_line pol LEFT JOIN pos_order po ON (po.id = pol.order_id)
                                JOIN product_product pp ON (pol.product_id = pp.id)
                                JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
                                JOIN product_category pct ON (pt.categ_id = pct.id)
                            WHERE 
                                (po.date_order + INTERVAL '7 hours')::date >= '%s' AND 
                                (po.date_order + INTERVAL '7 hours')::date <= '%s' AND
                                po."state" in ('paid','done','invoiced') AND
                                pct.id in %s
                            GROUP BY
                                pt.id, pol.product_id
                            ORDER BY
                                qty DESC
                            LIMIT %d
                        ) product_top
                    )
                    
                GROUP BY
                   product_categ_id
            """
            self._cr.execute(sql % (self.id, self.id, self.env.user.id, self.env.user.id, self.from_date, self.to_date,self.from_date, self.to_date,product_category_ids,self.limited))

        pivot_view_id = self.env.ref('ev_pos_report.top_selling_products_pivot').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('Top Selling Product'),
            'res_id': False,
            'res_model': 'top.selling.products.line',
            'views': [(pivot_view_id, 'pivot')],
            'context': dict(self.env.context),
            'domain': [('selling_product_id', '=', self.id)],
        }
        return action


class TopSellingProductsLine(models.TransientModel):
    _name = 'top.selling.products.line'
    _order = 'quantity DESC'

    selling_product_id = fields.Many2one('top.selling.products.report', 'Top Selling Products')
    product_categ_id = fields.Many2one('product.category', string='Product Category')
    quantity = fields.Float('Quantity')

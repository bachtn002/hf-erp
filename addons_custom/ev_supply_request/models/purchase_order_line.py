# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class PurchaseOrderline(models.Model):
    _inherit = 'purchase.order.line'

    x_listed_price = fields.Float('Liste price')
    x_note = fields.Text('Note')

    @api.onchange('product_id')
    def onchange_product_id(self):
        try:
            # super(PurchaseOrderline, self).onchange_product_id()

            if not self.product_id:
                return

            # Reset date, price and quantity since _onchange_quantity will provide default values
            self.price_unit = 0.0
            self.product_qty = 1.0

            # self.name = self._get_product_purchase_description(self.product_id)
            self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
            self.taxes_id = self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == self.env.company)

            warehouse_id = self.order_id.picking_type_id.warehouse_id
            region_id = warehouse_id.x_stock_region_id
            seller_id = 0
            check = False
            if region_id:
                query_region = self._sql_price_stock_reigon(region_id.id, self.product_id.product_tmpl_id.id, self.partner_id.id,
                                                            self.order_id.date_order.date())
                self._cr.execute(query_region)

                value_region = self._cr.dictfetchone()
                if value_region:
                    self.price_unit = value_region['price']
                    self.x_listed_price = value_region['x_listed_price']
                    seller_id = value_region['id']
                    check = True
            if check == False:
                query_warehouse = self._sql_price_stock_warehouse(warehouse_id.id, self.product_id.product_tmpl_id.id,
                                                                  self.partner_id.id,
                                                                  self.order_id.date_order.date())
                self._cr.execute(query_warehouse)
                value_warehouse = self._cr.dictfetchone()

                if value_warehouse:
                    self.price_unit = value_warehouse['price']
                    self.x_listed_price = value_warehouse['x_listed_price']
                    seller_id = value_warehouse['id']
                else:
                    query_price_location_false = self._sql_price_location_false(self.product_id.product_tmpl_id.id,
                                                                            self.partner_id.id,
                                                                            self.order_id.date_order.date())
                    self._cr.execute(query_price_location_false)
                    value_price_location_false = self._cr.dictfetchone()
                    if value_price_location_false:
                        self.price_unit = value_price_location_false['price']
                        self.x_listed_price = value_price_location_false['x_listed_price']
                        seller_id = value_price_location_false['id']
                    else:
                        self.price_unit = 0
                        self.x_listed_price = 0

            if seller_id != 0:
                seller = self.env['product.supplierinfo'].search([('id', '=', seller_id)])
                self.name = self._get_name_product(seller)
                if seller or not self.date_planned:
                    self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            else:
                self.name = '[' + self.product_id.default_code + '] ' + self.product_id.product_tmpl_id.name
                self.date_planned = self.date_order

        except Exception as e:
            raise ValidationError(e)

    def _get_name_product(self, supplinerinfo):
        try:
            name = ''
            if supplinerinfo.product_name and supplinerinfo.product_code:
                name = '[' + supplinerinfo.product_code + '] ' + supplinerinfo.product_name
            elif supplinerinfo.product_name and not supplinerinfo.product_code:
                name = supplinerinfo.product_name
            elif not supplinerinfo.product_name and supplinerinfo.product_code:
                name = supplinerinfo.product_code
            else:
                name = '[' + self.product_id.default_code + '] ' + self.product_id.product_tmpl_id.name
            return name
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        return

    def _sql_price_stock_warehouse(self, warehouse_id, product_id, partner_id, date):
        return """
            select b.id,
                   b.x_listed_price,
                   b.price
            from price_stock_warehouse a
                     join product_supplierinfo b on b.id = a.supplierinfo_id
                     join product_template c on c.id = b.product_tmpl_id
            where a.warehouse_id = %s
              and a.supplierinfo_id in (SELECT a.id
                                        from product_supplierinfo a
                                                 join res_partner b on b.id = a.name
                                                 join product_template c on c.id = a.product_tmpl_id
                                        where c.id = %s
                                          and b.id = %s
                                          and a.x_price_location = True
                                          and case
                                                  when a.date_start is not null and a.date_end is not null
                                                      then a.date_start  <= '%s' and a.date_end  >= '%s'
                                                  when a.date_start is null and a.date_end is not null
                                                      then a.date_end >= '%s'
                                                  when a.date_start is not null and a.date_end is null
                                                      then a.date_start <= '%s'
                                                  else 1 = 1
                                            end
                                        order by a.price asc)
            order by price asc
            limit 1
        """ % (warehouse_id, product_id, partner_id, date, date, date, date)

    def _sql_price_stock_reigon(self, region_id, product_id, partner_id, date):
        return """
            select b.id,
                   b.x_listed_price,
                   b.price
            from price_stock_region a
                     join product_supplierinfo b on b.id = a.supplierinfo_id
            where a.region_id = %s
              and a.supplierinfo_id in (SELECT a.id
                                        from product_supplierinfo a
                                                 join res_partner b on b.id = a.name
                                                 join product_template c on c.id = a.product_tmpl_id
                                        where c.id = %s
                                          and b.id = %s
                                          and a.x_price_location = True
                                          and case
                                                  when a.date_start is not null and a.date_end is not null
                                                      then a.date_start <= '%s' and a.date_end >= '%s'
                                                  when a.date_start is null and a.date_end is not null
                                                      then a.date_end  >= '%s'
                                                  when a.date_start is not null and a.date_end is null
                                                      then a.date_start  <= '%s'
                                                  else 1 = 1
                                            end
                                        order by a.price asc)
            order by price asc
            limit 1

        """ % (region_id, product_id, partner_id, date, date, date, date)

    def _sql_price_location_false(self, product_id, partner_id, date):
        return """
            SELECT b.id, a.x_listed_price, a.price
            from product_supplierinfo a
                       join res_partner b on b.id = a.name
                       join product_template c on c.id = a.product_tmpl_id
            where c.id = %s
                and b.id = %s
                and a.x_price_location = False
                and case
                        when a.date_start is not null and a.date_end is not null
                            then a.date_start <= '%s' and
                                 a.date_end >= '%s'
                        when a.date_start is null and a.date_end is not null
                            then a.date_end >= '%s'
                        when a.date_start is not null and a.date_end is null
                            then a.date_start <= '%s'
                        else 1 = 1
                  end
            order by a.price asc
            limit 1
        """ % (product_id, partner_id, date, date, date, date)


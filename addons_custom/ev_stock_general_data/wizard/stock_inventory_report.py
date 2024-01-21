# -*- coding: utf-8 -*-
from datetime import datetime, date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockInventoryReport(models.TransientModel):
    _name = 'stock.inventory.report'
    _description = 'Stock Inventory Report Wizard'

    from_date = fields.Date('From Date', default=fields.Date.today().strftime('%Y-%m-01'))
    to_date = fields.Date('To Date', default=fields.Date.today())
    type = fields.Selection([
        ('inventory', 'Inventory'),
        ('in_out', 'In Out')],
        'Type Report', default='inventory')

    region_ids = fields.Many2many('stock.region', string='Region')
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    categ_ids = fields.Many2many('product.category', string='Category')

    @api.onchange('region_ids')
    def set_domain_for_location_ids(self):
        if self.region_ids:
            return {'domain': {'location_ids': [('x_region_id.id', 'in', self.region_ids.ids)]}}
        else:
            return {'domain': {'location_ids': [(1, '=', 1)]}}

    def action_report(self):
        try:

            if self.type == 'in_out':
                action = self._query_stock_in_out_report()
            else:
                action = self._query_stock_inventory_report()
            return action
        except Exception as e:
            raise ValidationError(e)

    def action_view_inventory_report(self):
        try:
            return

        except Exception as e:
            raise ValidationError(e)

    def _query_stock_in_out_report(self):
        try:
            self.ensure_one()

            location_ids, product_ids, categ_ids, report_id = self._get_values()
            from_date = self.from_date.strftime('%Y-%m-%d')
            to_date = self.to_date.strftime('%Y-%m-%d')

            query = """
                INSERT INTO stock_in_out_report ( location, default_code, product, uom, qty_begin, qty_in, qty_out, 
                qty_end, report_id)
                SELECT location, default_code, product, uom, qty_begin, qty_in, qty_out, qty_end,
                %s as report_id
                FROM (
                        select b.name                                            as location,
           c.default_code                                    as default_code,
           d.name                                            as product,
           e.name                                            as uom,
           sum(a.qty_begin)                                  as qty_begin,
           sum(a.qty_in)                                     as qty_in,
           sum(a.qty_out)                                    as qty_out,
           sum(a.qty_begin) + sum(a.qty_in) - sum(a.qty_out) as qty_end
    from ( 
            select location_id, product_id, sum(qty_begin) qty_begin, 0 qty_in, 0 qty_out, 0 qty_end
         from (
                -- lấy giá trị trong view tổng hợp
                  SELECT DISTINCT ON (location_id, product_id) location_id,
                                                               product_id,
                                                               qty_end as qty_begin
                  from (select location_id, product_id, qty_end, date
                        from v_stock_in_out_report
                        where (location_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                          AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                          AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                          AND date = (select date::date as from_date
                                      from (select date_sync as date
                                            from stock_sync_monthly
                                            where date_sync::date < '%s'
                                              and state = 'done'
                                            order by date_sync DESC
                                            limit 2
                                           ) as d
                                      order by date
                                      limit 1)) as sgm
                  union all
                -- lấy sl nhập xuất từ đầu tháng tổng hợp tới ngày from_date
                  select xndk.location_id as location_id,
                         xndk.product_id as product_id,
                         sum(xndk.qty_in) - sum(xndk.qty_out) as qty_begin
                  from (
                           -- lấy sl nhập từ đầu tháng tổng hợp tới ngày from_date
                           SELECT a.location_dest_id    as location_id,
                                  a.product_id,
                                  case
                                      when a.product_uom_id != c.uom_id then (a.qty_done * d.factor)
                                      else qty_done end as qty_in,
                                  0                     as qty_out

                           FROM stock_move_line a
                                    join product_product b on b.id = a.product_id
                                    join product_template c on c.id = b.product_tmpl_id
                                    join uom_uom d on d.id = c.uom_id
                           where (location_dest_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                             AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                             AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                             and a.state = 'done'
                             and (a.date + interval '7 hours')::date < '%s'
                             and (a.date + interval '7 hours')::date >=
                                 (select date + interval '1 month' as from_date
                                  from (select date_sync as date
                                        from stock_sync_monthly
                                        where date_sync::date < '%s'
                                          and state = 'done'
                                        order by date_sync DESC
                                        limit 2
                                       ) as d
                                  order by date
                                  limit 1
                                 )::date

                           union all

                           SELECT a.location_id         as location_id,
                                  a.product_id,
                                  0                     as qty_in,
                                  case
                                      when a.product_uom_id != c.uom_id then (a.qty_done * d.factor)
                                      else qty_done end as qty_out

                           FROM stock_move_line a
                                    join product_product b on b.id = a.product_id
                                    join product_template c on c.id = b.product_tmpl_id
                                    join uom_uom d on d.id = c.uom_id
                           where (location_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                             AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                             AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                             and a.state = 'done'
                             and (a.date + interval '7 hours')::date < '%s'
                             and (a.date + interval '7 hours')::date >=
                                 (select date + interval '1 month' as from_date
                                  from (select date_sync as date
                                        from stock_sync_monthly
                                        where date_sync::date < '%s'
                                          and state = 'done'
                                        order by date_sync DESC
                                        limit 2
                                       ) as d
                                  order by date
                                  limit 1
                                 )::date
                       ) as xndk
                  group by xndk.location_id, xndk.product_id
              ) as dk
         group by dk.location_id, dk.product_id

         union all
-- lấy giá trị nhập xuất từ ngày from_date tới ngày to_date
         select xn.location_id,
                xn.product_id,
                0 as         qty_begin,
                sum(qty_in)  qty_in,
                sum(qty_out) qty_out,
                0            qty_end
         from (
                  -- lấy sl nhập từ sau kỳ tổng hợp tới ngày to_date
                  SELECT a.location_dest_id    as location_id,
                         a.product_id,
                         case
                             when a.product_uom_id != c.uom_id then (a.qty_done * d.factor)
                             else qty_done end as qty_in,
                         0                     as qty_out

                  FROM stock_move_line a
                           join product_product b on b.id = a.product_id
                           join product_template c on c.id = b.product_tmpl_id
                           join uom_uom d on d.id = c.uom_id
                  where (location_dest_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                    AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                    AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                    and a.state = 'done'
                    and (a.date + interval '7 hours')::date >= '%s'
                    and (a.date + interval '7 hours')::date <= '%s'

                  union all

                  -- lấy số lượng xuất từ sau kỳ tổng hợp tới ngày to_date

                  SELECT a.location_id         as location_id,
                         a.product_id,
                         0                        qty_in,
                         case
                             when a.product_uom_id != c.uom_id then (a.qty_done * d.factor)
                             else qty_done end as qty_out

                  FROM stock_move_line a
                           join product_product b on b.id = a.product_id
                           join product_template c on c.id = b.product_tmpl_id
                           join uom_uom d on d.id = c.uom_id
                  where (location_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                    AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                    AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                    and a.state = 'done'
                    and (a.date + interval '7 hours')::date >= '%s'
                    and (a.date + interval '7 hours')::date <= '%s'
              ) as xn
         group by xn.location_id, xn.product_id
         ) a
             join stock_location b on b.id = a.location_id
             join product_product c on c.id = a.product_id
             join product_template d on d.id = c.product_tmpl_id
             join uom_uom e on e.id = d.uom_id
    where b.usage = 'internal'
     and d.active = True
     --and d.type = 'product'
    group by location, c.default_code, product, uom
    order by location, default_code, product, uom

                ) as dt
                where dt.qty_begin != 0
          or dt.qty_out != 0
          or dt.qty_in != 0
          or dt.qty_end != 0
               ORDER BY location, default_code, product, uom
            """
            self.env.cr.execute(
                query % (report_id,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, from_date,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, from_date,
                         from_date,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, from_date,
                         from_date,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, from_date, to_date,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, from_date, to_date
                         ))
            self.env.cr.commit()
            # action = self.env['ir.actions.act_window']._for_xml_id('ev_stock_general_data.stock_in_out_report_action')
            # action['domain'] = [('report_id', '=', report_id)]
            return {
                'name': _('Stock In Out Report Action'),
                'view_mode': 'tree',
                'res_model': 'stock.in.out.report',
                'domain': [('report_id', '=', report_id)],
                'res_id': self.id,
                'type': 'ir.actions.act_window',
            }
            # return action
        except Exception as e:
            raise ValidationError(e)

    def _query_stock_inventory_report(self):
        try:
            self.ensure_one()

            location_ids, product_ids, categ_ids, report_id = self._get_values()
            to_date = self.to_date.strftime('%Y-%m-%d')
            query = """
                INSERT INTO stock_inventory_detail_report ( location, default_code, product, uom, qty, report_id)
                select location, default_code, product, uom, qty, report_id
                from (
                select b.name         as location,
                       c.default_code as default_code,
                       d.name         as product,
                       e.name         as uom,
                       sum(a.qty_end) as qty,
                       '%s'           as report_id
                from (
                        -- lấy dữ liệu từ dữ liệu tổng hợp gần nhất
                          SELECT DISTINCT ON (location_id, product_id) location_id,
                                                                       product_id,
                                                                       qty_end
                          from (select location_id, product_id, qty as qty_end, date
                                from v_stock_inventory_detail_report
                                where (location_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                                  AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                                  AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                                  AND date::date = (select date::date as from_date
                                    from (select date_sync as date
                                          from stock_sync_monthly
                                          where date_sync::date < '%s'
                                            and state = 'done'
                                          order by date_sync DESC
                                          limit 2
                                         ) as d
                                    order by date
                                    limit 1)) as sgm
                                    
                         union all
                
                -- lấy dữ liệu nhập từ ngày tổng hợp gần nhất tới ngày hiện tại
                         SELECT a.location_dest_id    as location_id,
                                a.product_id,
                                case
                                    when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                                    else qty_done end as qty_end
                         FROM stock_move_line a
                                  join product_product b on b.id = a.product_id
                                  join product_template c on c.id = b.product_tmpl_id
                                  join uom_uom d on d.id = c.uom_id
                         where (location_dest_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                           AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                           AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                           AND a.state = 'done'
                           and (a.date + interval '7 hours')::date <= '%s'
                           AND (a.date + interval '7 hours')::date >= (select date + interval '1 month' as from_date
                                                from (select date_sync as date
                                                      from stock_sync_monthly
                                                      where date_sync::date < '%s'
                                                        and state = 'done'
                                                      order by date_sync DESC
                                                      limit 2
                                                     ) as d
                                                order by date
                                                limit 1
                         )::date
                
                         union all
                
                -- lấy dữ liệu xuất từ ngày tổng hợp gần nhất tới ngày hiện tại
                         SELECT a.location_id          as location_id,
                                a.product_id,
                                case
                                    when a.product_uom_id != c.uom_id then -a.qty_done * d.factor
                                    else -qty_done end as qty_end
                         FROM stock_move_line a
                                  join product_product b on b.id = a.product_id
                                  join product_template c on c.id = b.product_tmpl_id
                                  join uom_uom d on d.id = c.uom_id
                         where (location_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                           AND (product_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                           AND (categ_id = ANY (string_to_array('%s', ',')::integer[]) or '%s' = '0')
                           AND a.state = 'done'
                           and (a.date + interval '7 hours')::date <= '%s'
                           AND (a.date + interval '7 hours')::date >= (select date + interval '1 month' as from_date
                                                from (select date_sync as date
                                                      from stock_sync_monthly
                                                      where date_sync::date < '%s'
                                                        and state = 'done'
                                                      order by date_sync DESC
                                                      limit 2
                                                     ) as d
                                                order by date
                                                limit 1
                         )::date
                     ) a
                         join stock_location b on b.id = a.location_id
                         join product_product c on c.id = a.product_id
                         join product_template d on d.id = c.product_tmpl_id
                         join uom_uom e on e.id = d.uom_id
                where b.usage = 'internal'
                    -- and d.type = 'product'
                group by location, c.default_code, product, uom
                order by location, default_code
                ) dt
                where dt.qty != 0
            """
            self.env.cr.execute(
                query % (report_id,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, to_date,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, to_date, to_date,
                         location_ids, location_ids, product_ids, product_ids, categ_ids, categ_ids, to_date, to_date))
            self.env.cr.commit()
            # action = self.env['ir.actions.act_window']._for_xml_id(
            #     'ev_stock_general_data.stock_inventory_detail_report_action')
            # action['domain'] = [('report_id', '=', report_id)]
            return {
                'name': _('Stock Inventory Details Report Action'),
                'view_mode': 'tree',
                'res_model': 'stock.inventory.detail.report',
                'domain': [('report_id', '=', report_id)],
                'res_id': self.id,
                'type': 'ir.actions.act_window',
            }
            # return action
        except Exception as e:
            raise ValidationError(e)

    def _get_values(self):
        try:
            location_ids = ','.join([str(idd) for idd in self.location_ids.ids]) if self.location_ids else '0'
            if self.region_ids:
                warehouse_ids = self.env.user.warehouse_ids
                stock_location_region = self.env['stock.location'].search([('x_region_id', 'in', self.region_ids.ids)])
                if warehouse_ids:
                    stock_locations = self.env['stock.location'].search([('x_warehouse_id', 'in', warehouse_ids.ids)])
                    if stock_locations:
                        location_true_ids = []
                        for stock_location in stock_locations:
                            if stock_location.id in stock_location_region.ids:
                                location_true_ids.append(stock_location.id)
                        if location_true_ids:
                            location_ids += ','
                            location_ids += ','.join([str(id) for id in location_true_ids])
                        else:
                            raise UserError(_('Location not in region! Please choose location'))
                elif not self.location_ids:
                    location_ids += ','
                    location_ids += ','.join([str(region) for region in stock_location_region.ids])
            if not self.region_ids and not self.location_ids:
                warehouse_ids = self.env.user.warehouse_ids
                if warehouse_ids:
                    stock_locations = self.env['stock.location'].search([('x_warehouse_id', 'in', warehouse_ids.ids)])
                    if stock_locations:
                        location_ids += ','.join([str(id) for id in stock_locations.ids])
                else:
                    location_ids = '0'
            product_ids = ','.join([str(idd) for idd in self.product_ids.ids]) if self.product_ids else '0'
            categ_ids = ','.join([str(idd) for idd in self.categ_ids.ids]) if self.categ_ids else '0'
            t = datetime.now().strftime('%Y%m%d%H%M%S')
            report_id = f'{t}.{self.env.user.id}'
            return location_ids, product_ids, categ_ids, report_id
        except Exception as e:
            raise ValidationError(e)

from odoo import api, fields, models, _


class StockMoveInOutValueAllReportStore(models.Model):
    _name = 'stock.move.in.out.value.all.report.store'
    _description = 'Stock Move In Out Value All Report Store'
    _auto = False

    def get_data(self, **kwargs):
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')

        product_ids = kwargs.get('product_ids')
        categ_ids = kwargs.get('categ_ids')

        sql = """
        select *
        from (select product_code,
             product_name,
             dv,
             SUM(tondau)                               sltondau,
             SUM(tondau_standard_price)                tondau_standard_price,
             -SUM(xuatkho)                             slxuatkho,
             -SUM(xuatkho_standard_price)              xuatkho_standard_price,
             SUM(nhapkho)                              slnhapkho,
             SUM(nhapkho_standard_price)               nhapkho_standard_price,
             SUM(tondau) + SUM(xuatkho) + SUM(nhapkho) sltoncuoi,
             SUM(tondau_standard_price) + SUM(xuatkho_standard_price) +
             SUM(nhapkho_standard_price)               toncuoi_standard_price
        from (
               select product_code,
                      product_name,
                      dv,
                      SUM(nhapkho_standard_price) + SUM(xuatkho_standard_price) tondau_standard_price,
                      SUM(nhapkho) + SUM(xuatkho)                               tondau,
                      0                                                         xuatkho_standard_price,
                      0                                                         xuatkho,
                      0                                                         nhapkho_standard_price,
                      0                                                         nhapkho

               from (
                        -- xuất kho
                        select f.default_code                   product_code,
                               f.name                           product_name,
                               g.name                           dv,
                               sum(a.balance)                   xuatkho_standard_price,
                               case
                                   when b.move_type != 'in_refund' then sum(a.quantity)
                                   else sum(-a.quantity) end as xuatkho,
                               0                                nhapkho_standard_price,
                               0                                nhapkho
                        from account_move_line a
                                 join account_move b on b.id = a.move_id
                                 join account_account c on c.id = a.account_id
                                 join product_product e on e.id = a.product_id
                                 join product_template f on f.id = e.product_tmpl_id
                                 join uom_uom g on g.id = f.uom_id

                        where b.state = 'posted'
                          and c.code in ('152', '1531', '1561')
                          and (f.categ_id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (e.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (a.balance < 0 or a.quantity < 0 or b.move_type = 'in_refund')
                          and to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <
                              to_date(%s, 'dd-mm-yyyy')

                        group by product_code, f.name, g.name, b.move_type
                        union all
                        -- nhập kho
                        select f.default_code  product_code,
                               f.name          product_name,
                               g.name          dv,
                               0               xuatkho_standard_price,
                               0               xuatkho,
                               sum(a.balance)  nhapkho_standard_price,
                               sum(a.quantity) nhapkho
                        from account_move_line a
                                 join account_move b on b.id = a.move_id
                                 join account_account c on c.id = a.account_id
                                 join product_product e on e.id = a.product_id
                                 join product_template f on f.id = e.product_tmpl_id
                                 join uom_uom g on g.id = f.uom_id

                        where b.state = 'posted'
                          and c.code in ('152', '1531', '1561')
                          and (f.categ_id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (e.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (a.balance > 0 or a.quantity > 0 and a.balance >= 0)
                          and b.move_type != 'in_refund'
                          and to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <
                              to_date(%s, 'dd-mm-yyyy')

                        group by product_code, f.name, g.name
                    ) as tondau
               group by product_code, product_name, dv

               union all

               select product_code,
                      product_name,
                      dv,
                      0                           tondau_standard_price,
                      0                           tondau,
                      SUM(xuatkho_standard_price) xuatkho_standard_price,
                      SUM(xuatkho)                xuatkho,
                      SUM(nhapkho_standard_price) nhapkho_standard_price,
                      SUM(nhapkho)                nhapkho

               from (
                        -- xuất trong kỳ
                        select f.default_code                   product_code,
                               f.name                           product_name,
                               g.name                           dv,
                               sum(a.balance)                   xuatkho_standard_price,
                               case
                                   when b.move_type != 'in_refund' then sum(a.quantity)
                                   else sum(-a.quantity) end as xuatkho,
                               0                                nhapkho_standard_price,
                               0                                nhapkho
                        from account_move_line a
                                 join account_move b on b.id = a.move_id
                                 join account_account c on c.id = a.account_id
                                 join product_product e on e.id = a.product_id
                                 join product_template f on f.id = e.product_tmpl_id
                                 join uom_uom g on g.id = f.uom_id

                        where b.state = 'posted'
                          and c.code in ('152', '1531', '1561')
                          and (f.categ_id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (e.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (a.balance < 0 or a.quantity < 0 or b.move_type = 'in_refund')
                          and to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
                              to_date(%s, 'dd-mm-yyyy')
                          and to_date(to_char(b.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                              to_date(%s, 'dd-mm-yyyy')

                        group by product_code, f.name, g.name, b.move_type

                        union all
                        -- nhập trong kỳ
                        select f.default_code  product_code,
                               f.name          product_name,
                               g.name          dv,
                               0               xuatkho_standard_price,
                               0               xuatkho,
                               sum(a.balance)  nhapkho_standard_price,
                               sum(a.quantity) nhapkho
                        from account_move_line a
                                 join account_move b on b.id = a.move_id
                                 join account_account c on c.id = a.account_id
                                 join product_product e on e.id = a.product_id
                                 join product_template f on f.id = e.product_tmpl_id
                                 join uom_uom g on g.id = f.uom_id

                        where b.state = 'posted'
                          and c.code in ('152', '1531', '1561')
                          and (f.categ_id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (e.id = ANY (string_to_array(%s, ',')::integer[]) or %s = '0')
                          and (a.balance > 0 or a.quantity > 0 and a.balance >= 0)
                          and b.move_type != 'in_refund'
                          and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >=
                              to_date(%s, 'dd-mm-yyyy')
                          and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <=
                              to_date(%s, 'dd-mm-yyyy')

                        group by product_code, f.name, g.name
                    ) as nhapxuat
               group by product_code, product_name, dv
           ) as bang
      group by product_code, product_name, dv
      ORDER BY product_name) as t
WHERE (sltoncuoi != 0 OR sltondau != 0 OR slnhapkho != 0 OR slxuatkho != 0);
        """

        params = (categ_ids, categ_ids, product_ids, product_ids,
                  from_date, categ_ids, categ_ids, product_ids,
                  product_ids, from_date,  product_ids,
                  categ_ids, categ_ids, product_ids, from_date, to_date,
                  categ_ids, categ_ids, product_ids, product_ids,
                  from_date, to_date)

        self._cr.execute(sql, params)
        return self._cr.dictfetchall()

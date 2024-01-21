# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class ReportRevenueByAge(models.TransientModel):
    _name = 'report.revenue.by.age'

    total_order = fields.Float('Order')
    amount_total = fields.Float('Amount total')
    group_age = fields.Selection([('20', 'Dưới 20'), ('20-30', '20 đến 30'),('30-40', '30 đến 40'),('40', 'Trên 40')])

    @api.model
    def load_views(self, views, options=None):
        sql = """
            DELETE from report_revenue_by_age where create_uid = %d;
            INSERT INTO report_revenue_by_age(total_order,amount_total,create_date,write_date,group_age,create_uid,write_uid)
            SELECT
            e.don tongdon,
            e.tong doanhthu,
            now() as create_date,
            now() as write_date,
            '20' nhom,
            (%d) as create_uid,
            (%d) as write_uid
            FROM(
                    SELECT
                    count(DISTINCT b.id) don,
                    sum(case when a.discount > 0 then a.price_unit*a.qty*(1-a.discount/100) else a.price_unit*a.qty end) tong
                    --sum(case when a.discount > 0 then 1 else 0 end) tong
                    FROM pos_order_line a, pos_order b, res_partner f
                    WHERE
                    a.order_id = b.id
                    and f.id = b.partner_id
                    and f.phone is not Null and f.phone != '0'
                    and f.rank_id not in ('9','6')
                    and date_part('year',age(current_date, f.x_birthday)) < 20
                    ) e
        UNION ALL
        SELECT
            e.don tongdon,
            e.tong doanhthu,
            now() as create_date,
            now() as write_date,
            '20-30' nhom,
            (%d) as create_uid,
            (%d) as write_uid
            FROM(
                    SELECT
                    count(DISTINCT b.id) don,
                    sum(case when a.discount > 0 then a.price_unit*a.qty*(1-a.discount/100) else a.price_unit*a.qty end) tong
                    --sum(case when a.discount > 0 then 1 else 0 end) tong
                    FROM pos_order_line a, pos_order b, res_partner f
                    WHERE
                    a.order_id = b.id
                    and f.id = b.partner_id
                    and f.phone is not Null and f.phone != '0'
                    and f.rank_id not in ('9','6')
                    and date_part('year',age(current_date, f.x_birthday)) >= 20
                    and date_part('year',age(current_date, f.x_birthday)) <= 30
                    ) e
            UNION ALL
            SELECT
            e.don tongdon,
            e.tong doanhthu,
            now() as create_date,
            now() as write_date,
            '30-40' nhom,
            (%d) as create_uid,
            (%d) as write_uid
            FROM(
                    SELECT
                    count(DISTINCT b.id) don,
                    sum(case when a.discount > 0 then a.price_unit*a.qty*(1-a.discount/100) else a.price_unit*a.qty end) tong
                    --sum(case when a.discount > 0 then 1 else 0 end) tong
                    FROM pos_order_line a, pos_order b, res_partner f
                    WHERE
                    a.order_id = b.id
                    and f.id = b.partner_id
                    and f.phone is not Null and f.phone != '0'
                    and f.rank_id not in ('9','6')
                    and date_part('year',age(current_date, f.x_birthday)) > 30
                    and date_part('year',age(current_date, f.x_birthday)) <= 40
                    ) e
                    UNION ALL
                    SELECT
            e.don tongdon,
            e.tong doanhthu,
            now() as create_date,
            now() as write_date,
            '40' nhom,
            (%d) as create_uid,
            (%d) as write_uid
            FROM(
                    SELECT
                    count(DISTINCT b.id) don,
                    sum(case when a.discount > 0 then a.price_unit*a.qty*(1-a.discount/100) else a.price_unit*a.qty end) tong
                    --sum(case when a.discount > 0 then 1 else 0 end) tong
                    FROM pos_order_line a, pos_order b, res_partner f
                    WHERE
                    a.order_id = b.id
                    and f.id = b.partner_id
                    and f.phone is not Null and f.phone != '0'
                    and f.rank_id not in ('9','6')
                    and date_part('year',age(current_date, f.x_birthday)) > 40
                    ) e;
            """
        self._cr.execute(sql % (self.env.user.id, self.env.user.id, self.env.user.id, self.env.user.id, self.env.user.id, self.env.user.id, self.env.user.id, self.env.user.id, self.env.user.id))

        options = options or {}
        result = {}

        toolbar = options.get('toolbar')
        result['fields_views'] = {
            v_type: self.fields_view_get(v_id, v_type if v_type != 'list' else 'tree',
                                         toolbar=toolbar if v_type != 'search' else False)
            for [v_id, v_type] in views
        }
        result['fields'] = self.fields_get()

        if options.get('load_filters'):
            result['filters'] = self.env['ir.filters'].get_filters(self._name, options.get('action_id'))

        #result = super(TopSellingProducts, self).load_views(views)
        return result
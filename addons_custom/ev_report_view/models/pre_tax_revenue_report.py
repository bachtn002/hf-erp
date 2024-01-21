from datetime import datetime

from odoo import api, fields, models, _


class PreTaxRevenueReport(models.TransientModel):
    _name = 'pre.tax.revenue.report'
    _description = 'Pre tax revenue report'

    shop_name = fields.Char("Shop name")
    revenue = fields.Float("Revenue", digits=(14, 0))
    revenue_refund = fields.Float("Revenue refund", digits=(14, 0))
    cost_price = fields.Float("Cost price", digits=(14, 0))
    profit = fields.Float("Profit", digits=(14, 0))
    report_id = fields.Char('Report ID')


class PreTaxRevenueReportWizard(models.TransientModel):
    _name = "pre.tax.revenue.report.wizard"
    _description = 'Pre tax revenue Report Wizard'

    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def create_report(self):
        self.ensure_one()
        from_date = self.from_date.strftime("%d/%m/%Y")
        if self.to_date:
            to_date = self.to_date.strftime("%d/%m/%Y")
        else:
            to_date = from_date

        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'

        sql = """
INSERT INTO
    pre_tax_revenue_report (
        shop_name,
        revenue,
        revenue_refund,
        cost_price,
        profit,report_id
    )
select shop_name
     , -sum(revenue)                                        revenue
     , sum(revenue_refund)                                  revenue_refund
     , sum(giavon)                                          giavon
     , -sum(revenue) - sum(revenue_refund) - sum(giavon) as loinhuan
     , %s as report_id
from (
         select ps.name        as shop_name,
                sum(a.balance) as revenue,
                0              as revenue_refund,
                0                 giavon
         from account_move_line a
                  join account_move b on a.move_id = b.id
                  join account_account c on c.id = a.account_id
                  join pos_session pss on pss.move_id = b.id
                  join pos_shop ps on ps.id = pss.x_pos_shop_id
         where c.code = '5111'
           and b.state = 'posted'
           and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd-mm-yyyy')
           and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd-mm-yyyy')
         group by shop_name

         union all

         select ps.name      as shop_name,
                0            as revenue,
                sum(a.balance) as revenue_refund,
                0               giavon
         from account_move_line a
                  join account_move b on a.move_id = b.id
                  join account_account c on c.id = a.account_id
                  join pos_session pss on pss.move_id = b.id
                  join pos_shop ps on ps.id = pss.x_pos_shop_id
         where c.code like concat('521', '%%')
           and b.state = 'posted'
           and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd-mm-yyyy')
           and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd-mm-yyyy')
         group by shop_name

         union all

         select f.name shop_name, 0 revenue, 0 revenue_refund, sum(a.debit)- sum(a.credit) as giavon
         from account_move_line a
                  join account_move b on b.id = a.move_id
                  join stock_move c on c.id = b.stock_move_id
                  join stock_picking d on d.id = c.picking_id
                  left join pos_session e on e.id = d.pos_session_id
                  left join pos_shop f on f.id = e.x_pos_shop_id
                  join account_account g on g.id = a.account_id
         where g.code = '632'
           and b.state = 'posted'
           and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date('%s', 'dd-mm-yyyy')
           and to_date(to_char(a.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date('%s', 'dd-mm-yyyy')
         group by shop_name
     ) as t
group by shop_name
       """
        self.env.cr.execute(sql % (
            report_id, from_date, to_date, from_date, to_date, from_date, to_date))
        self.env.cr.commit()
        return {
            'name': _('Pre tax revenue report'),
            'view_mode': 'tree',
            'res_model': 'pre.tax.revenue.report',
            'domain': [('report_id', '=', report_id)],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'search_view_id': self.env.ref('ev_report_view.pre_tax_revenue_report_search').id
        }

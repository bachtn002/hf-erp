from odoo import models, fields, api, exceptions,_
from datetime import datetime


class CashStatementReport(models.TransientModel):
    _name = 'cash.statement.report'
    _description = 'Bao cao kiem quy cuoi ngay'

    pos_shop_code = fields.Char('Shop Code')
    pos_name = fields.Char('Shop Name')
    address = fields.Char('Address')
    region_name = fields.Char('Region name')
    start_at = fields.Datetime('Start At')
    stop_at = fields.Datetime('Stop At')
    total_cash_app = fields.Float('Total Cash App', digits=(14, 0))
    total_cash_end_day = fields.Float('Total Cash End Day', digits=(14, 0))
    total_cash_deviant = fields.Float('Total Cash Deviant', digits=(14, 0))
    reason_money_difference = fields.Char('Reason Money Difference')
    report_id = fields.Char('Report ID')


class CashStatementReportWizard(models.TransientModel):
    _name = 'cash.statement.report.wizard'
    _description = 'Báo cáo kiểm quỹ cuối ngày'

    date = fields.Date('Date')

    def open_table_report(self):
        self.ensure_one()
        if self.date:
            date = self.date.strftime("%d/%m/%Y")
        t = datetime.now().strftime('%Y%m%d%H%M%S')
        report_id = f'{t}.{self.env.user.id}'
        sql = """
        insert into cash_statement_report (pos_shop_code, pos_name, address, region_name, start_at, stop_at, total_cash_app,
                                   total_cash_end_day,
                                   total_cash_deviant, reason_money_difference, report_id, create_date, write_date,
                                   create_uid, write_uid)
        select ps.code                                               pos_shop_code,
               ps.name                                               pos_name,
               ps.address                                            address,
               sr.name                                               region_name,
               start_at                          start_at,
               stop_at                           stop_at,
               p.x_money_total_cash_app                              total_cash_app,
               p.x_amount_total_cash_iput                            total_cash_end_day,
               p.x_amount_total_cash_iput - p.x_money_total_cash_app total_cash_deviant,
               p.x_reason_money_difference                           reason_money_difference,
               %s                                                    report_id,
               now(),
               now(),
               %d, %d
        from pos_shop ps
            left join stock_warehouse sw
        on ps.warehouse_id = sw.id
            left join stock_region sr on sw.x_stock_region_id = sr.id
            right join pos_session p on ps.id = p.x_pos_shop_id
        where to_date(to_char(p.start_at + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') = to_date('%s', 'dd/mm/yyyy')
        """

        self.env.cr.execute(sql % (report_id, self.env.user.id, self.env.user.id, date))
        self.env.cr.commit()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cash Statement Report Action'),
            'view_mode': 'tree',
            'res_model': 'cash.statement.report',
            'domain': [('report_id', '=', report_id)],
            'res_id': self.id,
        }

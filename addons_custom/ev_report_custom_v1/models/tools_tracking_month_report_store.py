from odoo import api, fields, models, _


class ToolsTrackingMonthReportStore(models.Model):
    _name = 'tools.tracking.month.report.store'
    _description = 'Tools Tracking Month Report Store'
    _auto = False

    def get_data(self, **kwargs):
        date_from = kwargs.get('from_date').strftime('%d/%m/%Y')
        date_to = kwargs.get('to_date').strftime('%d/%m/%Y')

        sql = """
        select a.x_code mataisan, a.name tentaisan, 
            (select amr.asset_remaining_value giatriconlai
                from account_move amr
                left join account_asset aa on aa.id = amr.asset_id
                where amr.state = 'posted'
                and aa.id = a.id
                and aa.state in ('open', 'close')
                and to_date(to_char(amr.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
            order by amr.write_date desc limit 1) as giatriconlai,
            COALESCE(am.amount_total, 0) gtkhauhao,
            COALESCE(to_char(am.date + INTERVAL '7 hours', 'mm/yyyy'), '') thangkhauhao
        from account_move am
        left join account_asset a on a.id = am.asset_id
        where am.state = 'posted'
        and a.x_asset_type IN ('tools', 'expenses')
        and a.state in ('open', 'close')
        and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') >= to_date(%s, 'dd/mm/yyyy')
        and to_date(to_char(am.date + INTERVAL '7 hours', 'dd/mm/yyyy'), 'dd/mm/yyyy') <= to_date(%s, 'dd/mm/yyyy')
        order by am.date
        """

        params = (date_to, date_from, date_to)

        self._cr.execute(sql, params)
        return self._cr.dictfetchall()

# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def action_validate_queue(self):
        try:
            query = """
                SELECT name
                    from stock_sync_monthly
                    where (date_sync + interval '1 month')::date > ('%s')::date
                    and state in ('sync', 'done')
                """
            self.env.cr.execute(query % self.accounting_date)
            values = self.env.cr.dictfetchall()
            if len(values) >= 1:
                raise UserError(_('you cannot take any action once aggregated data is available'))

            return super(StockInventory, self).action_validate_queue()
        except Exception as e:
            raise ValidationError(e)

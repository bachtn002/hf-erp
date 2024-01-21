# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, vals):
        try:
            res = super(StockPicking, self).create(vals)
            query = """
                SELECT state
                from stock_sync_monthly
                where (date_sync + interval '1 month')::date > now()::date
                and state in ('sync', 'done')
            """
            self.env.cr.execute(query)
            values = self.env.cr.dictfetchall()
            if len(values) >= 1:
                raise UserError(_('you cannot take any action once aggregated data is available'))
            return res
        except Exception as e:
            raise ValidationError(e)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        try:
            # nếu là move kiểm kê cho pass qua do đã check từ nút xác nhận
            if self.inventory_id:
                return super(StockMove, self).write(vals)
            for record in self:
                # Chặn hủy picking ở trạng thái hoàn thành
                # Chặn xác nhận hoàn thành picking
                if record.state != 'done' and vals.get('state') != 'done':
                    super(StockMove, record).write(vals)
                else:
                    if record.picking_id:
                        # kiem ke khong co picking chi co move
                        query = """
                                        SELECT name
                                        from stock_sync_monthly
                                        where (date_sync + interval '1 month')::date > ('%s')::date
                                        and state in ('sync', 'done')
                                    """
                        record.env.cr.execute(query % record.picking_id.create_date)
                        values = record.env.cr.dictfetchall()

                        if len(values) >= 1:
                            raise UserError(
                                _('you cannot take any action once aggregated data is available'))
                    super(StockMove, record).write(vals)
            return True
        except Exception as e:
            raise ValidationError(e)

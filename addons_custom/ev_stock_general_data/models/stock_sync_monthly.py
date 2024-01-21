# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockSyncMonthly(models.Model):
    _name = 'stock.sync.monthly'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Stock Synthesis Data Monthly'
    _order = 'create_date desc'

    name = fields.Char('Name', default=lambda self: _('New'), readonly=True, index=True)
    date = fields.Datetime('Date Sync', default=lambda x: datetime.today())
    month = fields.Integer('Month', default=lambda x: datetime.today().month, required=True, index=True)
    year = fields.Integer('Year', default=lambda x: datetime.today().year, required=True, index=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('sync', 'Synthesis'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        'State', default='draft', index=True, track_visibility='onchange')
    line_ids = fields.One2many('stock.sync.monthly.line', 'synthesis_id', 'Line ids')

    # ngày mặc định theo tháng để check dữ liệu
    date_sync = fields.Datetime('Date')

    @api.onchange('month')
    def _onchange_month(self):
        try:
            self.check_month()
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('year')
    def _onchange_year(self):
        try:
            self.check_year()
        except Exception as e:
            raise ValidationError(e)

    @api.constrains('month', 'year')
    def _constraint_month_year(self):
        try:
            month = str(self.month) if self.month > 9 else '0' + str(self.month)
            date = str(self.year) + '-' + month + '-01' + ' 12:00:00'
            date_sync = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            self.date_sync = date_sync
            self.check_sync()
        except Exception as e:
            raise ValidationError(e)

    def action_synthetic(self):
        try:
            self.ensure_one()
            self.check_month()
            self.check_year()
            self.check_sync()
            self.line_ids.unlink()
            if self.state == 'draft':
                self.date = datetime.now()
                self._insert_sync_monthly_line()
                self.state = 'sync'
            return
        except Exception as e:
            raise ValidationError(e)

    def action_confirm(self):
        try:
            self.ensure_one()
            if self.state == 'sync':
                self._insert_general_monthly()
                self.state = 'done'
            return
        except Exception as e:
            raise ValidationError(e)

    def action_cancel(self):
        try:
            sync_id = self.search([('id', '!=', self.id), ('date_sync', '>', self.date_sync),
                                   ('state', 'not in', ('draft', 'cancel'))], order='date_sync')
            if sync_id:
                code = sync_id.mapped('name')
                raise UserError(_('You must cancel the sync: %s to cancel this sync') % code)
            if self.state == 'sync':
                self.state = 'cancel'
            if self.state == 'done':
                query = """
                    DELETE FROM stock_general_monthly WHERE synthesis_id = %d
                """
                self.env.cr.execute(query % self.id)
                self.state = 'cancel'

        except Exception as e:
            raise ValidationError(e)

    def action_back_to_draft(self):
        try:
            self.ensure_one()
            if self.state == 'cancel':
                self.line_ids.unlink()
                self.state = 'draft'
        except Exception as e:
            raise ValidationError(e)

    def check_year(self):
        try:
            year = date.today().year
            if int(self.year) <= 2000 or int(self.year) > year:
                raise UserError(_('Invalid year please re-enter'))
        except Exception as e:
            raise ValidationError(e)

    def check_month(self):
        try:
            if int(self.month) < 1 or int(self.month) > 12:
                raise UserError(_('Invalid month please re-enter'))
        except Exception as e:
            raise ValidationError(e)

    def check_sync(self):
        try:
            if not self.month:
                raise UserError(_('You have not selected the month'))
            if not self.year:
                raise UserError(_('You have not selected the year'))
            year = date.today().year
            month = date.today().month
            if self.year > year or (self.year == year and self.month >= month):
                raise UserError(_('You can only synthesis the current month'))
            sync_id = self.search([('date_sync', '>=', self.date_sync), ('state', 'in', ('sync', 'done'))],
                                  order='date_sync', limit=1)
            if sync_id:
                raise UserError(
                    _('Month %s year %s have synthesized. You cannot continue synthesizing') % (
                        sync_id.month, sync_id.year))
        except Exception as e:
            raise ValidationError(e)

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_stock_general_data.stock_sync_monthly_xlsx/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def unlink(self):
        try:
            for rec in self:
                if rec.state in ('sync', 'done'):
                    raise UserError(_('You can only delete record in draft or cancel status'))
                self.line_ids.unlink()
                return super(StockSyncMonthly, self).unlink()
        except Exception as e:
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        try:
            res = super(StockSyncMonthly, self).create(vals)
            month = date.today().month
            year = date.today().year
            day = date.today().day
            prefix = f'SSM-{day:02d}{month:02d}{year % 100}/'
            seq = self.env['ir.sequence'].next_by_code('stock.sync.monthly')
            res.name = f'{prefix}{seq}'
            return res
        except Exception as e:
            raise ValidationError(e)

    def _insert_sync_monthly_line(self):
        try:
            month = str(self.month) if self.month >= 10 else '0' + str(self.month)
            from_date = str(self.year) + '-' + month + '-01'
            query = """
            INSERT INTO stock_sync_monthly_line (location_id, product_id, qty_begin, qty_in, qty_out, qty_end, month, year,
            synthesis_id, date, create_date, write_date,write_uid, create_uid, date_sync, uom_id, default_code, product_name)
            select location_id, product_id, qty_begin, qty_in, qty_out, qty_end, %d, %d, %d, now() - interval '7 hours',
             now() - interval '7 hours', now() - interval '7 hours', %d, %d, to_date('%s', 'yyyy-mm-dd HH:MM:SS'), uom_id,
             default_code, product_name
            from (
                select tb.location_id, tb.product_id,
                       sum(tb.qty_begin) as qty_begin,
                       sum(tb.qty_in)    as qty_in,
                       sum(tb.qty_out)   as qty_out,
                       sum(tb.qty_end)   as qty_end,
                       c.uom_id          as uom_id,
                       c.default_code    as default_code,
                       c.name            as product_name
                from (
                         -- lấy số tồn đầu kỳ
                         select nxdk.location_id   as location_id,
                                nxdk.product_id    as product_id,
                                nxdk.qty           as qty_begin,
                                0                as qty_in,
                                0                as qty_out,
                                (nxdk.qty + 0 - 0) as qty_end
                         from (
                                  -- lấy số lượng nhập đầu kỳ
                                  select location_id, product_id, sum(qty) as qty
                                  from (
                                           SELECT a.location_dest_id    as location_id,
                                                  a.product_id          as product_id,
                                                  case
                                                      when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                                                      else qty_done end as qty
                                           from stock_move_line a
                                                    join product_product b on b.id = a.product_id
                                                    join product_template c on c.id = b.product_tmpl_id
                                                    join uom_uom d on d.id = c.uom_id
                                                    join stock_location e on e.id = a.location_dest_id
                                           where a.state = 'done'
                                             and e.usage = 'internal'
                                             and (a.date + INTERVAL '7 hours')::date < '%s'
                                       ) as ndk
                                  group by location_id, product_id

                                  union all
                                  -- lấy số lượng xuất đầu kỳ
                                  select location_id, product_id, sum(-qty) as qty
                                  from (
                                           SELECT a.location_id         as location_id,
                                                  a.product_id          as product_id,
                                                  case
                                                      when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                                                      else qty_done end as qty
                                           from stock_move_line a
                                                    join product_product b on b.id = a.product_id
                                                    join product_template c on c.id = b.product_tmpl_id
                                                    join uom_uom d on d.id = c.uom_id
                                                    join stock_location e on e.id = a.location_id
                                           where a.state = 'done'
                                             and e.usage = 'internal'
                                             and (a.date + INTERVAL '7 hours')::date < '%s'
                                       ) as xdk
                                  group by location_id, product_id
                              ) as nxdk

                         union all

                         -- lấy số nhập xuất trong kỳ
                         select nxtk.location_id               as location_id,
                                nxtk.product_id                as product_id,
                                0                            as qty_begin,
                                nxtk.qty_in                    as qty_in,
                                nxtk.qty_out                   as qty_out,
                                (0 + nxtk.qty_in - nxtk.qty_out) as qty_end
                         from (
                                  -- lấy số lượng nhập trong kỳ
                                  select location_id, product_id, sum(qty_in) as qty_in, 0 as qty_out
                                  from (
                                           SELECT a.location_dest_id    as location_id,
                                                  a.product_id          as product_id,
                                                  case
                                                      when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                                                      else qty_done end as qty_in
                                           from stock_move_line a
                                                    join product_product b on b.id = a.product_id
                                                    join product_template c on c.id = b.product_tmpl_id
                                                    join uom_uom d on d.id = c.uom_id
                                                    join stock_location e on e.id = a.location_dest_id
                                           where a.state = 'done'
                                             and e.usage = 'internal'
                                             and (a.date + INTERVAL '7 hours')::date >= '%s'
                                             and (a.date + INTERVAL '7 hours')::date < to_date('%s', 'yyyy-mm-dd') + interval '1 month'
                                       ) as ntk
                                  group by location_id, product_id

                                  union all
                                  -- lấy số lượng xuất trong kỳ
                                  select location_id, product_id, 0 as qty_in, sum(qty_out) as qty_out
                                  from (
                                           SELECT a.location_id         as location_id,
                                                  a.product_id          as product_id,
                                                  case
                                                      when a.product_uom_id != c.uom_id then a.qty_done * d.factor
                                                      else qty_done end as qty_out
                                           from stock_move_line a
                                                    join product_product b on b.id = a.product_id
                                                    join product_template c on c.id = b.product_tmpl_id
                                                    join uom_uom d on d.id = c.uom_id
                                                    join stock_location e on e.id = a.location_id
                                           where a.state = 'done'
                                             and e.usage = 'internal'
                                             and (a.date + INTERVAL '7 hours')::date >= '%s'
                                             and (a.date + INTERVAL '7 hours')::date < to_date('%s', 'yyyy-mm-dd') + interval '1 month'
                                       ) as xtk
                                  group by location_id, product_id
                              ) as nxtk
                     ) as tb
                     join product_product b on b.id = tb.product_id
                     join product_template c on c.id = b.product_tmpl_id
                group by tb.location_id, tb.product_id, c.uom_id, c.default_code, c.name
                 ) as dt
            order by location_id, product_id
            """
            self.env.cr.execute(query % (
                self.month, self.year, self.id, self.write_uid.id, self.write_uid.id, from_date, from_date,
                from_date, from_date, from_date, from_date, from_date))
            self.env.cr.commit()

        except Exception as e:
            raise ValidationError(e)

    def _insert_general_monthly(self, ):
        try:
            query = """
            INSERT INTO stock_general_monthly (synthesis_id, location_id, product_id, qty_begin, qty_in, qty_out,
             qty_end, month, year, date, create_date, write_date,write_uid, create_uid, date_sync, default_code, product_name)
            select synthesis_id, location_id, product_id, qty_begin, qty_in, qty_out, qty_end, month, year, date,
             create_date, write_date,write_uid,create_uid, date_sync, default_code, product_name
            from stock_sync_monthly_line
            where synthesis_id = %d
            order by location_id, product_id
            """
            self.env.cr.execute(query % self.id)
            self.env.cr.commit()

        except Exception as e:
            raise ValidationError(e)

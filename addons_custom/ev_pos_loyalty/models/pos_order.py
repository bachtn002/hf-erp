# -*- coding: utf-8 -*-

from odoo import _, models, api, fields

import calendar
from dateutil.relativedelta import relativedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_from_ui(self, orders, draft=False):
        # Fix pos_restaurant module auto add loyalty_points
        order_ids = super(PosOrder, self).create_from_ui(orders, draft)
        for order in self.sudo().browse([o['id'] for o in order_ids]):
            if order.loyalty_points != 0 and order.partner_id:
                order.partner_id.loyalty_points -= order.loyalty_points
        return order_ids

    def _prepare_refund_values(self, current_session):
        values = super(PosOrder, self)._prepare_refund_values(current_session)
        values.update({'loyalty_points': -self.loyalty_points})
        return values

    @api.model
    def create(self, vals):
        res = super(PosOrder, self).create(vals)
        if 'state' in vals and vals['state'] == 'paid':
            res.create_loyalty_point_history()
            res.up_to_rank()
        return res

    def write(self, vals):
        res = super(PosOrder, self).write(vals)
        if 'state' in vals and vals['state'] == 'paid':
            self.create_loyalty_point_history()
            self.up_to_rank()
        return res

    def up_to_rank(self):
        if self.loyalty_points == 0 or not self.partner_id:
            return
        points = self.partner_id.loyalty_points
        partner_id = self.partner_id
        date_rank = self.date_order
        customer_rank = self.env['customer.rank'].search([('point', '<=', points)], order='point desc', limit=1)
        if customer_rank:
            loyalty = self.session_id.config_id.loyalty_id
            month = loyalty.x_month_expire
            expire_date = date_rank + relativedelta(months=month)
            expire_date = self.get_last_day_of_month(expire_date)
            if customer_rank.id != partner_id.x_rank_id.id or not partner_id.x_rank_id:
                partner_id.x_rank_id = customer_rank.id
                partner_id.x_date_rank = date_rank
                rank_history_obj = self.env['customer.rank.history']
                args = {
                    'partner_id': partner_id.id,
                    'rank_id': customer_rank.id,
                    'date_rank': date_rank,
                    'loyalty_program_id': loyalty.id,
                    'month_expire': month,
                    'expire_date': expire_date,
                    'point': points,
                    'pos_order_id': self.id
                }
                rank_history_obj.create(args)

    def create_loyalty_point_history(self):
        if self.loyalty_points == 0 or not self.partner_id:
            return
        loyalty = self.session_id.config_id.loyalty_id
        month = loyalty.x_month_expire
        expire_date = fields.Date.today() + relativedelta(months=month)
        expire_date = self.get_last_day_of_month(expire_date)

        CustomerPointHistory = self.env['customer.point.history']

        domain = [('partner_id', '=', self.partner_id.id),
                ('expire_date', '=', expire_date),
                ('state', '=', 'available')]
        history = CustomerPointHistory.search(domain)
        if history:
            point = history.point + self.loyalty_points
            history.write({
                'point': point
                })
        else:
            CustomerPointHistory.create({
                'partner_id': self.partner_id.id,
                'point': self.loyalty_points,
                'expire_date': expire_date,
                'state': 'available',
                'month_expire': month
                })
        self.partner_id.loyalty_points += self.loyalty_points

    @staticmethod
    def get_last_day_of_month(date):
        year = date.year
        month = date.month
        month_range = calendar.monthrange(year, month)
        date = date.strftime('%Y-%m-') + str(month_range[1])
        return date

    def _get_fields_for_order_line(self):
        res = super(PosOrder, self)._get_fields_for_order_line()
        res += ['is_rank_discount']
        return res

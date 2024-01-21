# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil import relativedelta


class CustomerRankHistory(models.Model):
    _name = 'customer.rank.history'
    _order = 'create_date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Customer rank history'

    partner_id = fields.Many2one('res.partner', string="Partner")
    rank_id = fields.Many2one('customer.rank', string="Rank")
    date_rank = fields.Date('Date rank')
    point = fields.Float(string="Point")
    pos_order_id = fields.Many2one('pos.order', 'Pos order')
    loyalty_program_id = fields.Many2one('loyalty.program', 'Loyalty Program')
    month_expire = fields.Integer('Month Expire')
    expire_date = fields.Date('Expire date')

    def check_rank_customer(self):
        today = fields.Date.today()
        self._get_rank_customer(today)

    def _get_rank_customer(self, date):
        customer_rank_history_ids = self.search([('expire_date', '=', date)])
        for customer_rank_history in customer_rank_history_ids:
            partner_id = customer_rank_history.partner_id
            current_point = partner_id.loyalty_points
            customer_rank = self.env['customer.rank'].search([('point', '<=', current_point)], order='point desc',limit=1)
            if customer_rank:
                date_rank = datetime.strftime(date, '%Y-%m-%d')
                month = customer_rank_history.month_expire
                x_date = datetime.strptime(date_rank, '%Y-%m-%d')
                if month > 0:
                    expired = self._get_date_expire(date, month)
                else:
                    expired = None
                if customer_rank.id != partner_id.x_rank_id.id:
                    self._update_customer_rank(partner_id, customer_rank, date, expired, customer_rank_history, month)
                else:
                    print()

    def _update_customer_rank(self, partner_id, rank_id, date_rank, expired, customer_rank_history, month):
        partner_id.x_rank_id = rank_id.id
        partner_id.x_date_rank = date_rank
        args = {
            'partner_id': partner_id.id,
            'rank': rank_id.id,
            'date': date_rank,
            'loyalty_program_id': customer_rank_history.customer_rank_history.id,
            'month_expire': month,
            'expire_date': expired
        }
        self.create(args)

    def _get_date_expire(self, date, month):
        expired = (date + relativedelta(months=month))
        month = expired.month
        year = expired.year
        expired = monthrange(year, month)
        expired = datetime(year, month, expired[1])
        expired = datetime.strftime(expired, '%Y-%m-%d')
        expired = datetime.strptime(str(expired), '%Y-%m-%d')





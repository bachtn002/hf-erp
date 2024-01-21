# -*- coding: utf-8 -*-

from odoo import _, models, api, fields

import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


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

    # @api.model
    # def create(self, vals):
    #     res = super(PosOrder, self).create(vals)
    #     if 'state' in vals and vals['state'] == 'paid':
    #         res.create_loyalty_point_history()
    #     return res

    # Thêm tính năng gửi tin nhắn zns nên cập nhật điểm khách hàng bên gửi zns
    # def write(self, vals):
    #     res = super(PosOrder, self).write(vals)
    #     if 'state' in vals and vals['state'] == 'paid':
    #         self.create_loyalty_point_history()
    #     return res

    def create_loyalty_point_history(self):
        if self.loyalty_points == 0 or not self.partner_id:
            return
        loyalty = self.session_id.config_id.loyalty_id
        expire_date = fields.Datetime.now()
        CustomerPointHistory = self.env['customer.point.history']

        domain = [('partner_id', '=', self.partner_id.id)]
        history = CustomerPointHistory.search(domain)
        type = ''
        if self.loyalty_points > 0:
            type = 'accumulate_point'
        elif self.loyalty_points < 0:
            type = 'focus_point'
        CustomerPointHistory.create({
            'partner_id': self.partner_id.id,
            'points': self.loyalty_points,
            'expire_date': self.date_order,
            'type': type,
            'order_id': self.id
        })
        self.partner_id.loyalty_points += self.loyalty_points

    def update_loyalty_points_history(self):
        try:
            query = """ 
                select id, partner_id, date_order, loyalty_points, x_pos_order_refund_id
                from pos_order
                where partner_id is not null
                  and state in ('paid', 'done')
                  and (date_order+ interval '7 hours')::date >= '2021-10-01'
                  and (date_order+ interval '7 hours')::date <= '2021-12-04'
                  and loyalty_points != 0
            """
            self._cr.execute(query)
            datas = self._cr.dictfetchall()
            for data in datas:
                history = self.env['customer.point.history'].sudo().search(
                    [('partner_id', '=', data['partner_id']), ('order_id', '=', data['id'])])
                if history:
                    continue

                type = ''
                if data['loyalty_points'] > 0:
                    type = 'accumulate_point'
                elif data['loyalty_points'] < 0:
                    type = 'focus_point'
                # cập nhật lại điểm
                if data['x_pos_order_refund_id'] != None:
                    partner = self.env['res.partner'].sudo().search([('id', '=', data['partner_id'])])
                    partner.loyalty_points += data['loyalty_points']
                # ghi lại lịch sử điểm
                self.env['customer.point.history'].sudo().create({
                    'partner_id': data['partner_id'],
                    'points': data['loyalty_points'],
                    'expire_date': data['date_order'],
                    'type': type,
                    'order_id': data['id']
                })
                self.env.cr.commit()
        except Exception as e:
            raise ValidationError(e)

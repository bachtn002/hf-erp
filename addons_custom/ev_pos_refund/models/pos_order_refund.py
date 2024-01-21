# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta


class PosOrderRefund(models.Model):
    _inherit = 'pos.order'

    x_pos_order_refund_id = fields.Many2one('pos.order', string='Pos Order Refund', store=True, readonly=True)

    x_allow_return = fields.Boolean(string='Accountant Confirm', default=False, readonly=True)

    x_note_return = fields.Text(string='Note Return')

    x_pos_send_return = fields.Boolean(string='Pos return', default=False)

    x_picking_count_refund = fields.Integer(compute='_compute_picking_count_refund')

    x_reason_refuse = fields.Text('Reason Refuse')

    @api.depends('picking_count')
    def _compute_picking_count_refund(self):
        for record in self:
            record.x_picking_count_refund = record.picking_count

    def action_refuse_return(self):
        try:
            if not self.x_pos_send_return:
                return
            self.x_pos_send_return = False
            if self.x_note_return:
                self.x_note_return += _(' (Refuse)')
        except Exception as e:
            raise ValidationError(e)

    def action_send_return(self):
        self._check_data_allow_refund()
        if not self.x_note_return:
            raise UserError(_('No reason entered'))
        self.x_pos_send_return = True

    def allow_return(self):
        self._check_data_allow_refund()
        if self.x_allow_return == True:
            return
        else:
            self.x_allow_return = True

    def _prepare_refund_values(self, current_session):
        self.ensure_one()
        return {
            'name': self.name + _(' REFUND'),
            'session_id': current_session.id,
            'date_order': fields.Datetime.now(),
            'pos_reference': self.pos_reference,
            'lines': False,
            'amount_tax': -self.amount_tax,
            'amount_total': -self.amount_total,
            'amount_paid': 0,
            'x_pos_order_refund_id': self.id,
        }

    def refund(self):
        """Create a copy of order  for refund order"""
        check_refund_order = self.env['pos.order'].search([('x_pos_order_refund_id', '=', self.id)])
        if not check_refund_order:
            if self.x_allow_return == True:
                refund_orders = self.env['pos.order']
                for order in self:
                    order._check_data_allow_refund()
                    # When a refund is performed, we are creating it in a session having the same config as the original
                    # order. It can be the same session, or if it has been closed the new one that has been opened.
                    current_session = order.session_id.config_id.current_session_id
                    if not current_session or current_session.state in ('queued'):
                        raise UserError(_('To return product(s), you need to open a session in the POS %s',
                                          order.session_id.config_id.display_name))
                    refund_order = order.copy(
                        order._prepare_refund_values(current_session)
                    )
                    for line in order.lines:
                        PosOrderLineLot = self.env['pos.pack.operation.lot']
                        for pack_lot in line.pack_lot_ids:
                            PosOrderLineLot += pack_lot.copy()
                        line.copy(line._prepare_refund_data(refund_order, PosOrderLineLot))
                    refund_orders |= refund_order

                return {
                    'name': _('Return Products'),
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'res_id': refund_orders.ids[0],
                    'view_id': False,
                    'context': self.env.context,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                }
            else:
                raise UserError(_('Refund order has passed, please contact your accountant'))
        else:
            raise UserError(_('The order cannot continue to be return'))

    def action_print_order(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/ev_pos_refund.report_template_pos_order_view/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def _check_data_allow_refund(self):
        day_allow = self.company_id.x_allow_return_before_day
        if ((datetime.today() + timedelta(hours=7)).date() - (self.date_order + timedelta(hours=7)).date()).days > day_allow:
            raise UserError(
                _('You are only allowed to submit your order for approval after a maximum of %s days') % (day_allow))
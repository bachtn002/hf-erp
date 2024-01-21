# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, timedelta, timezone

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PosSession(models.Model):
    _inherit = 'pos.session'

    x_cash_statement_ids = fields.One2many('cash.statement', 'pos_session_id', string='Cash Statement', no_create=True)

    x_amount_total_cash = fields.Float(string='Amount Total', compute='_compute_amount_total')

    x_check_cash_statement = fields.Boolean(default=False, compute='_compute_check_cash_statement')

    x_difference_amount = fields.Float(string='Amount difference', default=0, compute='_compute_difference_amount')

    x_address_company = fields.Char(compute='_compute_address_company')

    x_amount_total_cash_app = fields.Float(compute='_compute_x_amount_total_cash_app')

    x_time_print = fields.Char()

    x_reason_money_difference = fields.Text(string='Reason')

    x_money_total_cash_app = fields.Float(string='Amount Money App', store=True,
                                          compute='_compute_x_amount_total_cash_app')

    x_amount_total_cash_iput = fields.Float(store=True, compute='_compute_x_amount_total_cash_app')

    x_cash_fund_balance = fields.Monetary('Cash fund balance')

    def action_pos_session_closing_control(self):
        if not self.x_check_cash_statement:
            raise UserError(_('Please enter the cash statement before closing the session!'))
        elif self.x_difference_amount != 0:
            if not self.x_reason_money_difference:
                raise UserError(_('Please enter the reason before closing the session!'))
        self._check_pos_session_balance()
        for session in self:
            if session.state == 'closed':
                raise UserError(_('This session is already closed.'))
            session.write({'state': 'closing_control', 'stop_at': fields.Datetime.now()})
            if not session.config_id.cash_control:
                session.action_pos_session_close()
                try:
                    if session.x_pos_shop_id.warehouse_id.out_minus:
                        for picking in self.picking_ids:
                            if picking.state != 'done':
                                picking.button_validate()
                except Exception as e:
                    raise ValidationError(e)

    @api.depends('order_ids')
    def _compute_x_amount_total_cash_app(self):
        for record in self:
            total_amount = 0
            for order in record.order_ids:
                for pay in order.payment_ids:
                    if pay.payment_method_id.is_cash_count == True:
                        total_amount += pay.amount
            record.x_amount_total_cash_app = total_amount + record.x_pos_shop_id.cash_fund_balance
            # số dư tiền mặt trên phần mềm in báo cáo
            record.x_money_total_cash_app = record.x_amount_total_cash_app
            record.x_amount_total_cash_iput = record.x_amount_total_cash

    @api.depends('company_id')
    def _compute_address_company(self):
        for record in self:
            record.x_address_company = 'Địa chỉ: '
            for r in record.company_id:
                if r.street:
                    record.x_address_company = record.x_address_company + ' ' + r.street
                if r.street2:
                    record.x_address_company = record.x_address_company + ' ' + r.street2
                if r.city:
                    record.x_address_company = record.x_address_company + ' ' + r.city
                if r.state_id:
                    record.x_address_company = record.x_address_company + ' ' + r.state_id.name
                if r.country_id:
                    record.x_address_company = record.x_address_company + ' ' + r.country_id.name

    @api.depends('x_amount_total_cash')
    def _compute_difference_amount(self):
        for record in self:
            record.x_difference_amount = record.x_amount_total_cash - record.x_amount_total_cash_app

    @api.depends('x_cash_statement_ids')
    def _compute_check_cash_statement(self):
        for record in self:
            if record.x_cash_statement_ids:
                record.x_check_cash_statement = True
            else:
                record.x_check_cash_statement = False

    @api.depends('x_cash_statement_ids', 'x_cash_statement_ids.amount')
    def _compute_amount_total(self):
        for record in self:
            record.x_amount_total_cash = 0
            for r in record.x_cash_statement_ids:
                record.x_amount_total_cash += r.amount

    def print_cash_statement_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_cash_statement.cash_statement_xlsx/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def print_cash_statement_pdf(self):
        tz = pytz.timezone(self.env.user.tz) or pytz.utc
        date = pytz.utc.localize(
            datetime.strptime(datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M'), '%d/%m/%Y %H:%M')).astimezone(tz)
        self.x_time_print = datetime.strftime(date, '%d/%m/%Y %H:%M')
        if self.x_difference_amount != 0:
            if self.x_reason_money_difference:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/report/pdf/ev_cash_statement.report_template_cash_statement_internal_view/%s' % self.id,
                    'target': 'new',
                    'res_id': self.id,
                }
            else:
                raise UserError(_('You have not entered the reason for the money difference'))
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': '/report/pdf/ev_cash_statement.report_template_cash_statement_internal_view/%s' % self.id,
                'target': 'new',
                'res_id': self.id,
            }

    def input_cash_statement(self):
        for record in self:
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 500000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 200000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 100000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 50000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 20000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 10000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 5000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 2000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 1000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': record.id,
                'denominations': 500,
            })
            self.env.cr.commit()

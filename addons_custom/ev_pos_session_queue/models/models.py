# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import random
from dateutil.relativedelta import relativedelta
from datetime import datetime


class PosSessionQueue(models.Model):
    _inherit = 'pos.session'

    state = fields.Selection(selection_add=[('queued', 'Queued')],ondelete={'queued': 'cascade'})
    #x_stop_at = fields.Datetime(string='Closing Date', readonly=True, copy=False)

    @api.constrains('config_id')
    def _check_pos_config(self):
        if self.search_count([
            ('state', 'not in', ('closed', 'queued')),
            ('config_id', '=', self.config_id.id),
            ('rescue', '=', False)
        ]) > 1:
            raise ValidationError(_("Another session is already opened for this point of sale."))

    def action_pos_session_closing_control_queue(self):
        #self.action_pos_session_closing_control()
        if not self.x_check_cash_statement:
            raise UserError(_('Please enter the cash statement before closing the session!'))
        elif self.x_difference_amount != 0:
            if not self.x_reason_money_difference:
                raise UserError(_('Please enter the reason before closing the session!'))
        pos_order = self.env['pos.order'].search([('state','=', 'draft'),('session_id','=', self.id)])
        if len(pos_order) > 0:
            raise UserError(_('Session have an order in draft!'))
        self._check_pos_session_balance()
        for session in self:
            if session.state == 'closed':
                raise UserError(_('This session is already closed.'))
        self.write({'state': 'queued'})

        number = random.randint(0, 3)
        if number == 1:
            self.sudo().with_delay(channel='root.action_pos_session_closing_control_2',max_retries=3).action_pos_session_closing_control()
        elif number == 2:
            self.sudo().with_delay(channel='root.action_pos_session_closing_control',
                                   max_retries=3).action_pos_session_closing_control()
        elif number == 3:
            self.sudo().with_delay(channel='root.action_pos_session_closing_control_2',
                                   max_retries=3).action_pos_session_closing_control()
        else:
            self.sudo().with_delay(channel='root.action_pos_session_closing_control',
                                   max_retries=3).action_pos_session_closing_control()
        # self.sudo().with_delay(channel='root.action_pos_session_closing_control',
        #                        max_retries=3).action_pos_session_closing_control()

    def open_frontend_cb(self):
        """Open the pos interface with config_id as an extra argument.

        In vanilla PoS each user can only have one active session, therefore it was not needed to pass the config_id
        on opening a session. It is also possible to login to sessions created by other users.

        :returns: dict
        """
        if not self.ids:
            return {}
        if self.state == 'opened':
            start_at = (self.start_at + relativedelta(hours=7)).date()
            date_now = datetime.now() + relativedelta(hours=7)
            date_now = date_now.date()
            if start_at < date_now:
                raise UserError(_('You cannot continue to sell the previous day.'))
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.config_id._get_pos_base_url() + '?config_id=%d' % self.config_id.id,
        }


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def open_session_cb(self, check_coa=True):
        """ new session button

        create one if none exist
        access cash control interface if enabled or start a session
        """
        self.ensure_one()
        if not self.current_session_id or self.current_session_id.state == 'queued':
            self._check_company_journal()
            self._check_company_invoice_journal()
            self._check_company_payment()
            self._check_currencies()
            self._check_profit_loss_cash_journal()
            self._check_payment_method_ids()
            self._check_payment_method_receivable_accounts()
            self.env['pos.session'].create({
                'user_id': self.env.uid,
                'config_id': self.id
            })
        return self.open_ui()

    def open_ui(self):
        """Open the pos interface with config_id as an extra argument.

        In vanilla PoS each user can only have one active session, therefore it was not needed to pass the config_id
        on opening a session. It is also possible to login to sessions created by other users.

        :returns: dict
        """
        self.ensure_one()
        if self.current_session_id.state == 'opened':
            start_at = (self.current_session_id.start_at + relativedelta(hours=7)).date()
            date_now = datetime.now() + relativedelta(hours=7)
            date_now = date_now.date()
            if start_at < date_now:
                raise UserError(_('You cannot continue to sell the previous day.'))
        # check all constraints, raises if any is not met
        self._validate_fields(set(self._fields) - {"cash_control"})
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_pos_base_url() + '?config_id=%d' % self.id,
            'target': 'self',
        }


class StockQuantQueue(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                   in_date=None):
        if location_id.usage != 'internal':
            return quantity, in_date
        else:
            return super(StockQuantQueue, self)._update_available_quantity(product_id,location_id,quantity,lot_id,package_id,owner_id,in_date)

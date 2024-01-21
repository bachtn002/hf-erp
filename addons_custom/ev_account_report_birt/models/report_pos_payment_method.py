# -*- coding: utf-8 -*-
import odoo.tools.config as config

from odoo import models, fields, api, exceptions
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class ReportPosPaymentMethod(models.TransientModel):
    _name = 'report.pos.payment.method'

    name = fields.Char('Name', default='Report Pos Payment Method')
    from_date = fields.Date('From date')
    to_date = fields.Date('To date')
    pos_payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    report_pos_payment_method_line_ids = fields.One2many('report.pos.payment.method.line',
                                                         'report_pos_payment_method_id', string='Detail')

    def _compute_value(self, account_id, date, analytic_account_id):
        self.env.cr.execute(
            "SELECT COALESCE(SUM(balance), 0) "
            "FROM account_move_line aml, account_move am "
            "WHERE aml.move_id=am.id "
            "AND am.state='%s' "
            "AND aml.date<'%s' "
            "AND aml.account_id=%s"
            "AND aml.analytic_account_id=%s"
            % ('posted', str(date), str(account_id.id), str(analytic_account_id.id)))
        return self.env.cr.fetchone()[0] or 0.000

    def _compute_debit(self, from_date, to_date, account_id, analytic_account_id):
        self.env.cr.execute(
            "SELECT COALESCE(SUM(debit), 0) "
            "FROM account_move_line aml, account_move am "
            "WHERE aml.move_id=am.id "
            "AND am.state='%s' "
            "AND aml.date>='%s'"
            "AND aml.date<='%s'"
            "AND aml.account_id=%s"
            "AND aml.analytic_account_id=%s"
            % ('posted', str(from_date), str(to_date), str(account_id.id), str(analytic_account_id.id)))
        return self.env.cr.fetchone()[0] or 0.000

    def _compute_credit(self, from_date, to_date, account_id, analytic_account_id):
        self.env.cr.execute(
            "SELECT COALESCE(SUM(credit), 0) "
            "FROM account_move_line aml, account_move am "
            "WHERE aml.move_id=am.id "
            "AND am.state='%s' "
            "AND aml.date>='%s'"
            "AND aml.date<='%s'"
            "AND aml.account_id=%s"
            "AND aml.analytic_account_id=%s"
            % ('posted', str(from_date), str(to_date), str(account_id.id), str(analytic_account_id.id)))
        return self.env.cr.fetchone()[0] or 0.000

    def action_filter_all(self):
        try:
            if self.report_pos_payment_method_line_ids:
                for record in self.report_pos_payment_method_line_ids:
                    record.unlink()
            if self.pos_payment_method_id:
                pos_config_ids = self.env['pos.config'].search(
                    [('payment_method_ids', 'in', self.pos_payment_method_id.id)])
                pos_shop_ids = self.env['pos.shop'].search([('pos_config_ids', 'in', pos_config_ids.ids)])
                account_id = self.env['account.account']
                if self.pos_payment_method_id.is_cash_count:
                    account_id = self.pos_payment_method_id.cash_journal_id.default_account_id
                else:
                    account_id = self.pos_payment_method_id.receivable_account_id
                if pos_shop_ids:
                    for pos_shop_id in pos_shop_ids:
                        intital_balance = self._compute_value(account_id, self.from_date,
                                                              pos_shop_id.analytic_account_id)
                        debit = self._compute_debit(self.from_date, self.to_date,
                                                    account_id, pos_shop_id.analytic_account_id)
                        credit = self._compute_credit(self.from_date, self.to_date,
                                                      account_id, pos_shop_id.analytic_account_id)
                        self.env['report.pos.payment.method.line'].create({
                            'account_analytic_id': pos_shop_id.analytic_account_id.id,
                            'pos_payment_method_id': self.pos_payment_method_id.id,
                            'intital_balance': intital_balance,
                            'debit': debit,
                            'credit': credit,
                            'report_pos_payment_method_id': self.id,
                        })
                        self.env.cr.commit()
        except Exception as e:
            raise ValidationError(e)

    def print_report_payment_method_xlsx(self):
        self.action_filter_all()
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_account_report_birt.pos_payment_method_xlsx/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

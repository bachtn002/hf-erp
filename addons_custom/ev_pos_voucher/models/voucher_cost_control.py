# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class VoucherCostControl(models.Model):
    _name = 'voucher.cost.control'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string="Name", required=True)
    from_date = fields.Date('From Date', default=lambda x: datetime.today())
    to_date = fields.Date('To Date', default=lambda x: datetime.today())
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('voucher.cost.control.line', 'voucher_cost_control_id',
                                            string='Voucher Cost Control Line')
    move_count = fields.Float('Count Move',default=0, compute='_compute_count_move')
    date = fields.Date('Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('synthesized', 'Synthesized'),
        ('posted', 'Posted'),
        ('cancel', 'Cancel')],
        string='state', default='draft'
    )

    @api.depends('line_ids', 'line_ids.account_move_id')
    def _compute_count_move(self):
        for record in self:
            move_ids = []
            for rec in record.line_ids:
                if rec.account_move_id:
                    move_ids.append(rec.account_move_id.id)
            move_ids = list(set(move_ids))
            record.move_count = len(move_ids)

    def action_view_move(self):
        self.ensure_one()
        move_ids = []
        for record in self:
            for rec in record.line_ids:
                if rec.account_move_id:
                    move_ids.append(rec.account_move_id.id)
        move_ids = list(set(move_ids))
        action = self.env.ref('account.action_move_journal_line')
        result = action.sudo().read()[0]
        result['domain'] = [('id', 'in', move_ids)]
        return result

    def unlink(self):
        if self.state == 'draft':
            return super(VoucherCostControl, self).unlink()
        raise UserError(_('Thông báo! Bạn chỉ có thể xóa khi ở trạng thái Nháp'))

    @api.onchange('from_date', 'to_date')
    def onchange_date(self):
        if self.from_date and self.to_date:
            from_date = self.from_date.strftime('%d/%m/%Y')
            to_date = self.to_date.strftime('%d/%m/%Y')
            self.name = _('Voucher cost control from ') + str(from_date) + 'đến ' + str(to_date)

    def action_synthetic(self):
        self.ensure_one()
        if self.state == 'synthesized':
            return
        self._synthetic_voucher_payment()
        if len(self.line_ids) > 0:
            self.state = 'synthesized'

    def _synthetic_voucher_payment(self):
        pos_payment_ids = self.env['pos.payment'].search([('payment_date','>=',self.from_date),('payment_date','<=',self.to_date),('x_is_voucher_checked','=',False),
                                                          ('payment_method_id.x_is_voucher','=',True)])
        for pos_payment in pos_payment_ids:
            analytic_account_id = 0
            account_expense_id = 0
            account_expense_item_id = 0
            if pos_payment.x_lot_id.x_release_id.analytic_account_id:
                analytic_account_id = pos_payment.x_lot_id.x_release_id.analytic_account_id.id
            else:
                analytic_account_id = pos_payment.pos_order_id.x_pos_shop_id.analytic_account_id.id
            if pos_payment.x_lot_id.x_release_id.account_expense_id:
                account_expense_id = pos_payment.x_lot_id.x_release_id.account_expense_id.id
            if pos_payment.x_lot_id.x_release_id.account_expense_item_id:
                account_expense_item_id = pos_payment.x_lot_id.x_release_id.account_expense_item_id.id

            self.env['voucher.cost.control.line'].create({
                'voucher_cost_control_id': self.id,
                'lot_id': pos_payment.x_lot_id.id if pos_payment.x_lot_id else None,
                'used_date': pos_payment.payment_date,
                'amount': pos_payment.amount,
                'pos_order_id': pos_payment.pos_order_id.id,
                'pos_payment_id': pos_payment.id,
                'account_id': account_expense_id,
                'analytic_account_id': analytic_account_id,
                'account_expense_item_id': account_expense_item_id,
            })
            pos_payment.x_is_voucher_checked = True

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'posted':
            return
        self._create_account_move()
        # self.date = datetime.now()
        self.state = 'posted'

    def action_set_to_draft(self):
        self.ensure_one()
        if self.state == 'draft':
            return
        if self.state == 'synthesized':
            for line in self.line_ids:
                line.pos_payment_id.x_is_voucher_checked = False
        self.line_ids.unlink()
        self.state = 'draft'

    def action_cancel(self):
        for line in self.line_ids:
            line.account_move_id.button_draft()
            line.account_move_id.with_context(force_delete=True).unlink()
            line.pos_payment_id.x_is_voucher_checked = False
        self.state = 'cancel'
        # self.date = ''

    def _create_account_move(self):
        journal_id = self.env['account.journal'].search([('code','=','KHAC')], limit=1)
        for line in self.line_ids:
            move_lines = []
            debit_move_vals = {
                'name': line.lot_id.name,
                'ref': self.name,
                'date': self.date,
                'account_id': line.account_id.id if line.account_id else None,
                'debit': line.amount,
                'credit': 0.0,
                'x_account_expense_item_id': line.account_expense_item_id.id if line.account_expense_item_id else None,
                'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None
            }
            move_lines.append((0, 0, debit_move_vals))
            a = self
            # Ghi sổ thu/chi của công ty
            credit_move_vals = {
                'name': line.lot_id.name,
                'ref': self.name,
                'date': self.date,
                'account_id': line.pos_payment_id.payment_method_id.cash_journal_id.default_account_id.id,
                'debit': 0.0,
                'credit': line.amount,
                'x_account_expense_item_id': line.account_expense_item_id.id if line.account_expense_item_id else None,
                'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None
            }
            move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': self.name,
                'date': self.date,
                'journal_id': journal_id.id,
                'line_ids': move_lines,
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            line.account_move_id = move_id.id

    def print_move_voucher(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_pos_voucher.move_voucher_xlsx/%s' % self.id,
            'target': 'new',
            'res_id': self.id,
        }

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': ('/report/xlsx/ev_pos_voucher.voucher_cost_control_xlsx/%s' % self.id),
            'target': 'new',
            'res_id': self.id,
        }


class VoucherCostControlLine(models.Model):
    _name = 'voucher.cost.control.line'

    voucher_cost_control_id = fields.Many2one(comodel_name='voucher.cost.control', string='Voucher Cost Control', ondelete='cascade')
    lot_id = fields.Many2one('stock.production.lot', 'Voucher')
    used_date = fields.Date(string='Used Date')
    amount = fields.Float('Amount')
    pos_order_id = fields.Many2one('pos.order', 'Pos Order')
    pos_payment_id = fields.Many2one('pos.payment', 'Pos Payment')
    account_move_id = fields.Many2one('account.move', 'Account Move')

    product_id = fields.Many2one('product.product', 'Product', related='lot_id.product_id')
    account_id = fields.Many2one('account.account', 'Accounting Account')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    account_expense_item_id = fields.Many2one('account.expense.item', 'Account Expense Item')



# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UpdateProductRelease(models.TransientModel):
    _name = 'update.product.release'

    card_id = fields.Many2one('product.product', string='Card')
    blank_card_id = fields.Many2one('product.product', string='Blank card')
    date = fields.Date('Date')
    expired_type = fields.Selection(string='Expired type',
                                    selection=[('fixed', 'Fixed'), ('flexible', 'Flexible')])
    validity = fields.Integer('Validity')
    expired_date = fields.Date('Expired date')
    use_type = fields.Selection(string='Use type', selection=[('fixed', 'Fixed'), ('flexible', 'Flexible')],
                                help=_(
                                    "predefined method: when customer A buys a voucher, only customer A can use that voucher, Flexible method: when customer A buys a voucher, anyone who has that voucher can use it"))

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    account_expense_item_id = fields.Many2one('account.expense.item', 'Account Expense Item')
    account_expense_id = fields.Many2one('account.account', 'Account Expense')

    def action_update(self):
        try:
            product_release = self.env['product.release'].browse(self._context.get('active_id'))
            for record in product_release:
                if self.card_id:
                    record.card_id = self.card_id
                # if self.blank_card_id:
                #     record.blank_card_id = self.blank_card_id
                if self.analytic_account_id:
                    record.analytic_account_id = self.analytic_account_id
                if self.account_expense_item_id:
                    record.account_expense_item_id = self.account_expense_item_id
                if self.account_expense_id:
                    record.account_expense_id = self.account_expense_id

                if self.date:
                    record.date = self.date

                if self.expired_type and self.expired_type == 'flexible':
                    record.validity = self.validity
                    record.expired_type = 'flexible'
                    record.expired_date = None
                    for line in record.stock_production_lot_ids:
                        if line.x_state not in ('used', 'expired', 'destroy', 'lock'):
                            line.expiration_date = self.expired_date
                elif self.expired_type and self.expired_type == 'fixed':
                    record.expired_type = 'fixed'
                    if self.expired_date:
                        record.expired_date = self.expired_date
                        for line in record.stock_production_lot_ids:
                            if line.x_state not in ('used', 'expired', 'destroy', 'lock'):
                                line.expiration_date = self.expired_date
                else:
                    if self.expired_date:
                        record.expired_date = self.expired_date
                        for line in record.stock_production_lot_ids:
                            if line.x_state not in ('used', 'expired', 'destroy', 'lock'):
                                line.expiration_date = self.expired_date
                    if self.validity:
                        record.validity = self.validity

                if self.use_type:
                    record.use_type = self.use_type

        except Exception as e:
            raise ValidationError(e)

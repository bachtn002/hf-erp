# -*- coding: utf-8 -*-


from odoo import models, fields, api


class CashStatementInput(models.TransientModel):
    _name = 'cash.statement.input'

    denominations_500000 = fields.Integer(string='500.000')
    denominations_200000 = fields.Integer(string='200.000')
    denominations_100000 = fields.Integer(string='100.000')
    denominations_50000 = fields.Integer(string='50.000')
    denominations_20000 = fields.Integer(string='20.000')
    denominations_10000 = fields.Integer(string='10.000')
    denominations_5000 = fields.Integer(string='5.000')
    denominations_2000 = fields.Integer(string='2.000')
    denominations_1000 = fields.Integer(string='1.000')
    denominations_500 = fields.Integer(string='500')

    def create_cash_statement(self):
        pos_session_id = self.env['pos.session'].browse(self._context.get('active_id')).id

        for record in self:
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 500000,
                'quantity': record.denominations_500000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 200000,
                'quantity': record.denominations_200000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 100000,
                'quantity': record.denominations_100000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 50000,
                'quantity': record.denominations_50000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 20000,
                'quantity': record.denominations_20000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 10000,
                'quantity': record.denominations_10000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 5000,
                'quantity': record.denominations_5000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 2000,
                'quantity': record.denominations_2000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 1000,
                'quantity': record.denominations_1000,
            })
            self.env.cr.commit()
            self.env['cash.statement'].create({
                'pos_session_id': pos_session_id,
                'denominations': 500,
                'quantity': record.denominations_500,
            })
            self.env.cr.commit()

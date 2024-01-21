# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ConfirmDateTmp(models.TransientModel):
    _name = 'confirm.date.tmp'

    stock_transfer_id = fields.Many2one('stock.transfer', 'Stock Transfer')
    date = fields.Datetime('Date', default=fields.Datetime.now)

    def action_done(self):
        if self.stock_transfer_id.state == 'ready':
            # self.stock_transfer_id.out_date = self.date
            self.stock_transfer_id.action_transfer(False)
        else:
            self.stock_transfer_id.in_date = self.date
            self.stock_transfer_id.action_receive()

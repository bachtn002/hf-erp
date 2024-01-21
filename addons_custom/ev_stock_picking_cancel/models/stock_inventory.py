# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPickingCancel(models.Model):
    _inherit = 'stock.inventory'

    def action_cancel_inventory(self):
        for res in self:
            for move in res.move_ids:
                move.action_force_cancel()
            res.write({'state': 'cancel'})

    def action_cancel_draft(self):
        super(StockPickingCancel, self).action_cancel_draft()
        if self.state == 'draft':
            if len(self.move_ids) > 0:
                sql="""
                    DELETE FROM stock_move_line b
                    USING stock_move a 
                    WHERE 
                    a.inventory_id = %s
                    and a.id = b.move_id;
                    DELETE FROM stock_move
                    WHERE 
                    inventory_id = %s;
                """
                self._cr.execute(sql % (str(self.id), str(self.id)))
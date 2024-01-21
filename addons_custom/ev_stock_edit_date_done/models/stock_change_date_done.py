# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class StockChangeDateDone(models.TransientModel):
    _name = "stock.change.date.done"
    _description = "Change Date Done"

    new_date = fields.Datetime('Date done', required=True, help="The actual date of completion.")

    @api.model
    def default_get(self, fields):
        res = super(StockChangeDateDone, self).default_get(fields)
        picking = self.env[self._context['active_model']].browse(self._context['active_id'])
        if 'new_date' in fields and 'new_date' not in res:
            res['new_date'] = picking.date_done
        return res

    def change_date_done(self):
        """ Change the completion date of picking and move """
        self.ensure_one()
        if self._context['active_model'] == 'stock.picking' and self.env['stock.picking'].browse(self._context['active_id']).date_done != self.new_date:
            picking = self.env['stock.picking'].browse(self._context['active_id'])
            lang = self.env['res.lang'].search([('code', '=', self.env.lang)], limit=1)
            if lang:
                date_format = lang.date_format
            if picking.company_id.period_lock_date:
                if picking.company_id.period_lock_date > self.new_date.date():
                    raise UserError(
                        _('Bạn đã khóa kỳ vào ngày ' + picking.company_id.period_lock_date.strftime(date_format)))
            picking.update({'date_done': self.new_date})
            for move in picking.move_lines:
                # inventory_line = self.env['stock.inventory.line'].search([
                #     ('product_id', '=', move.product_id.id), '|', ('location_id', '=', move.location_id.id),
                #     ('location_id', '=', move.location_dest_id.id),
                #     ('inventory_date', '>=', self.new_date), ('inventory_id.state', 'in', ('confirm', 'done'))], limit=1)
                # if inventory_line:
                #     raise ValidationError(_('You cannot cancel transfers after inventory.'))
                move.update({'date': self.new_date})
                for move_line in move.move_line_ids:
                    move_line.update({'date': self.new_date})
                account_move = self.env['account.move'].search([('stock_move_id', '=', move.id)], limit=1)
                if account_move:
                    query = """
                            update account_move a 
                            set date = (b.date + INTERVAL '7 hours')::date
                            from stock_move_line b, stock_move c 
                            where 
                            a.stock_move_id = c.id
                            and c.id = b.move_id
                            and a.id = %d;
                            update account_move_line a 
                            set date = (b.date + INTERVAL '7 hours')::date
                            from stock_move_line b, stock_move c, account_move d
                            where 
                            d.stock_move_id = c.id
                            and c.id = b.move_id
                            and a.move_id = d.id
                            and d.id = %d;
                            update account_journal_general a 
                            set date = (b.date + INTERVAL '7 hours')::date
                            from stock_move_line b, stock_move c, account_move d
                            where 
                            d.stock_move_id = c.id
                            and c.id = b.move_id
                            and a.account_move_id = d.id
                            and d.id = %d;
                            """
                    self._cr.execute(query % (account_move.id,account_move.id,account_move.id))
        return {'type': 'ir.actions.act_window_close'}
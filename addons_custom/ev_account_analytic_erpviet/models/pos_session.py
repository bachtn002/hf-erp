# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_closing_control(self):
         super(PosSession, self).action_pos_session_closing_control()
         self._update_analytic_account()

    def _update_analytic_account(self):
        #update account move
        if not self.config_id.x_pos_shop_id.analytic_account_id:
            raise UserError(_("Analytic Account has not been configured. Please contact the administrator!"))
        if self.move_id:
            sql1="""
                UPDATE account_move_line a 
                SET analytic_account_id = %s, contra_account_id = %s
                where  move_id = %s;
            """
            account_receivable_id = self.env['ir.property']._get('property_account_receivable_id', 'res.partner')
            self._cr.execute(sql1 % (self.config_id.x_pos_shop_id.analytic_account_id.id, account_receivable_id.id, self.move_id.id))
        sql = """
                UPDATE account_move_line d 
                SET analytic_account_id = %s 
                FROM account_bank_statement a, account_bank_statement_line b, account_move c
                WHERE a.pos_session_id = %s
                and a.id = b.statement_id
                and b.move_id = c.id 
                and c.id = d.move_id;
             """
        self._cr.execute(sql % (self.config_id.x_pos_shop_id.analytic_account_id.id, self.id))
        start_at = (self.start_at + relativedelta(hours=7)).date()
        stop_at = (self.stop_at + relativedelta(hours=7)).date()
        if start_at < stop_at:
            stop_at_tmp = str(start_at) + ' 16:59:00'
            stop_at_obj = datetime.strptime(stop_at_tmp, '%Y-%m-%d %H:%M:%S')
            stop_at_time = str(stop_at_obj.date())
            if self.move_id:
                sql2 = """
                    UPDATE account_move_line a 
                    SET date = '%s'
                    where  move_id = %s;
                    
                    UPDATE account_move a 
                    SET date = '%s'
                    where  id = %s;
                    
                    UPDATE account_move_line d 
                    SET date = '%s' 
                    FROM account_bank_statement a, account_bank_statement_line b, account_move c
                    WHERE a.pos_session_id = %s
                    and a.id = b.statement_id
                    and b.move_id = c.id 
                    and c.id = d.move_id;
                    
                    UPDATE account_move c
                    SET date = '%s' 
                    FROM account_bank_statement a, account_bank_statement_line b, account_move_line d
                    WHERE a.pos_session_id = %s
                    and a.id = b.statement_id
                    and b.move_id = c.id 
                    and c.id = d.move_id;
                """
                self._cr.execute(sql2 % (stop_at_time, self.move_id.id, stop_at_time, self.move_id.id, stop_at_time, self.id, stop_at_time, self.id))
                sql3 = """
                update pos_session set stop_at = '%s' where id = %s;
                
                UPDATE stock_picking a 
                SET date_done = '%s'
                WHERE 
                pos_session_id = %s;
                
                UPDATE stock_move_line a
                SET date = '%s' 
                FROM stock_picking b, stock_move c 
                WHERE 
                c.picking_id = b.id 
                and a.move_id = c.id 
                and b.pos_session_id = %s;
                
                UPDATE stock_move a
                SET date = '%s' 
                FROM stock_picking b 
                WHERE 
                a.picking_id = b.id 
                and b.pos_session_id = %s;
                
                UPDATE account_move c
                SET date = '%s' 
                FROM stock_move a, stock_picking b 
                WHERE 
                a.picking_id = b.id 
                and c.stock_move_id = a.id
                and b.pos_session_id = %s;
                
                
                UPDATE account_move_line d
                SET date = '%s' 
                FROM stock_move a, stock_picking b, account_move c
                WHERE 
                a.picking_id = b.id 
                and c.stock_move_id = a.id
                and d.move_id = c.id
                and b.pos_session_id = %s;
                """
                self._cr.execute(sql3 % (stop_at_obj, self.id, stop_at_obj, self.id, stop_at_obj, self.id, stop_at_obj, self.id, stop_at_time, self.id, stop_at_time, self.id))



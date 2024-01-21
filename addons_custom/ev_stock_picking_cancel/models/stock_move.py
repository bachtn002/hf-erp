# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError,ValidationError
from odoo.tools.float_utils import float_round, float_compare


class StockMoveCancel(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        if any(move.state == 'done' for move in self):
            for move in self:
                if move.state == 'cancel':
                    continue
                inventory_line = self.env['stock.inventory.line'].search([
                    ('product_id','=',move.product_id.id),'|',('location_id','=',move.location_id.id),('location_id','=',move.location_dest_id.id),
                    ('inventory_date','>=',move.date),('inventory_id.state','in',('confirm','done'))], limit=1)
                if inventory_line:
                    raise ValidationError(_('You cannot cancel transfers after inventory.'))
                move.mapped('move_line_ids')._action_cancel_done()
                move.write({'state': 'cancel', 'date': fields.Datetime.now()})
                account_move = self.env['account.move'].search([('stock_move_id','=',move.id)])
                for account_move_id in account_move:
                    if account_move_id.sudo()._check_fiscalyear_lock_date():
                        account_move_id.sudo().button_cancel()
                        account_move_id.stock_move_id = False
                for account_move_id in account_move:
                    account_move_id.with_context(force_delete = True).unlink()
                for value in move.stock_valuation_layer_ids:
                    value.sudo().unlink()
        else:
            super(StockMoveCancel, self)._action_cancel()
        return True

    def action_force_cancel(self):
        if any(move.state == 'done' for move in self):
            for move in self:
                if move.state == 'cancel':
                    continue
                move.mapped('move_line_ids')._action_cancel_done()
                move.write({'state': 'cancel', 'date': move.create_date})
                account_move = self.env['account.move'].search([('stock_move_id','=',move.id)])
                for account_move_id in account_move:
                    if account_move_id.sudo()._check_fiscalyear_lock_date():
                        account_move_id.sudo().button_cancel()
                        account_move_id.stock_move_id = False
                for account_move_id in account_move:
                    account_move_id.with_context(force_delete = True).unlink()
                for value in move.stock_valuation_layer_ids:
                    value.sudo().unlink()
        else:
            super(StockMoveCancel, self)._action_cancel()
        return True

    def _action_set_to_draft(self):
        if any(move.state == 'cancel' for move in self):
            for move in self:
                move.write({'state': 'draft'})


class StockMoveLineCancel(models.Model):
    _inherit = 'stock.move.line'

    def _action_cancel_done(self):
        self = self.with_context(do_not_run_create_correction_svl = True)
        Quant = self.env['stock.quant']
        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].create(
                                    {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                )
                                ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            continue
                    elif ml.move_id.inventory_id:
                        continue
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_to_delete |= ml
        for item in ml_to_delete:
            if item.qty_done == 0:
                item.state = 'draft'
        ml_to_delete.unlink()
        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                rounding = ml.product_uom_id.rounding
                if not ml.location_dest_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
                    extra_qty = ml.qty_done - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_dest_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                if not ml.location_dest_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_dest_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_dest_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_dest_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_dest_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_dest_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_dest_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            done_ml |= ml
        (self - ml_to_delete).with_context(bypass_reservation_update=True, do_not_run_create_correction_svl = True).write({
            'product_uom_qty': 0.00,
            'qty_done': 0.00,
            'date': fields.Datetime.now(),
        })

    @api.model
    def _create_correction_svl(self, move, diff):
        if self.env.context.get('do_not_run_create_correction_svl'):
            return
        return super(StockMoveLineCancel, self)._create_correction_svl(move, diff)

# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        super(StockPicking, self)._action_done()
        if self.id != False:
            out_stock_transfer = self.env['stock.transfer'].search([('out_picking_id','=',self.id)],limit=1)
            if out_stock_transfer:
                if len(out_stock_transfer.transfer_line_ids) == 0:
                    for move in self.move_lines:
                        stock_transfer_line = self.env['stock.transfer.line'].create({
                            'product_id': move.product_id.id,
                            'name': move.product_id.name,
                            'quantity': move.product_qty,
                            'out_quantity': move.quantity_done,
                            'product_uom': move.product_id.uom_id.id,
                            'stock_transfer_id': out_stock_transfer.id
                        })
                        move.x_out_transfer_line_id = stock_transfer_line.id
                    out_stock_transfer.out_date = self.date_done
                else:
                    for move in self.move_lines:
                        if move.x_out_transfer_line_id:
                            if move.quantity_done:
                                move.x_out_transfer_line_id.out_quantity = move.quantity_done
                        else:
                            stock_transfer_line = self.env['stock.transfer.line'].create({
                                'product_id': move.product_id.id,
                                'name': move.product_id.name,
                                'quantity': move.product_qty,
                                'out_quantity': move.quantity_done,
                                'product_uom': move.product_id.uom_id.id,
                                'stock_transfer_id': out_stock_transfer.id
                            })
                            move.x_out_transfer_line_id = stock_transfer_line.id
                out_stock_transfer.action_transfer(True)
                if out_stock_transfer.out_date != False:
                    for m_line in self.move_line_ids:
                        sql = """UPDATE stock_move_line set date = '%s' where id = %d;
                                        """
                        self._cr.execute(sql % (out_stock_transfer.out_date, m_line.id))
                else:
                    out_stock_transfer.out_date = self.date_done
            in_stock_transfer = self.env['stock.transfer'].search([('in_picking_id', '=', self.id)], limit=1)
            if in_stock_transfer:
                in_stock_transfer.in_date = self.date_done
                if in_stock_transfer.in_date < in_stock_transfer.out_date:
                    raise UserError(_('Bạn không thể nhận trước ngày xuất'))
                in_stock_transfer.state = 'done'
                for move in self.move_lines:
                    if not move.x_in_transfer_line_id and move.product_qty != 0:
                        raise UserError(_('Bạn không thể nhận sản phẩm không có trong đơn chuyển ' + move.product_id.product_tmpl_id.name))
                    if move.x_in_transfer_line_id:
                        move.x_in_transfer_line_id.in_quantity = move.quantity_done
                if in_stock_transfer.in_date != False:
                    for m_line in self.move_line_ids:
                        sql = """UPDATE stock_move_line set date = '%s' where id = %d;
                                        """
                        self._cr.execute(sql % (in_stock_transfer.in_date, m_line.id))
                else:
                    in_stock_transfer.in_date = self.date_done

    def action_cancel(self):
        for line in self:
            super(StockPicking, line).action_cancel()
            stock_transfer_id = self.env['stock.transfer'].search([('out_picking_id','=',line.id)], limit=1)
            if stock_transfer_id.id != False:
                stock_transfer_id.state = 'cancel'

    def button_validate(self):
        self.ensure_one()
        scan_barcode = False
        if len(self.move_ids_without_package) < 1 and self.state == 'draft' and self.picking_type_code == 'internal':
            scan_barcode = True
        if scan_barcode == False:
            return super(StockPicking, self).button_validate()
        else:
            check_available_quantity = True
            for line in self.move_line_ids_without_package:
                # Reserve new quants and create move lines accordingly.
                forced_package_id = line.package_level_id.package_id or None
                available_quantity = self.env['stock.quant']._get_available_quantity(line.product_id, line.location_id,
                                                                                     package_id=forced_package_id)
                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                available_quantity = float_round(available_quantity, precision_digits=precision_digits,
                                                 rounding_method='HALF-UP')
                if available_quantity < line.qty_done:
                    check_available_quantity = False
                    break
            if check_available_quantity:
                return super(StockPicking, self).button_validate()
            else:
                stock_tranfer_id = self.env['stock.transfer'].search([('name', '=', self.origin)], limit=1)
                transfer_line_args = []
                for line in self.move_line_ids_without_package:
                    move_vals = {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom': line.product_uom_id.id,
                        'quantity': line.qty_done,
                        'stock_transfer_id': stock_tranfer_id.id,
                        'note': ''
                    }
                    transfer_line_args.append(move_vals)
                stock_tranfer_id.transfer_line_ids = transfer_line_args
                self.move_line_ids_without_package.unlink()
                self.move_line_ids.unlink()
                self.unlink()
                stock_tranfer_id.state = 'draft'
                stock_tranfer_id.action_confirm()
                stock_tranfer_id.action_check_available()
        # if self.picking_type_code == 'internal':
        #     for move_line in self.move_line_ids_without_package:
        #         if move_line.quantity_done > move_line.reserved_quantity:
        #             raise UserError(_("Bạn không thể điều chuyển sản phẩm không đủ tồn kho"))
        return
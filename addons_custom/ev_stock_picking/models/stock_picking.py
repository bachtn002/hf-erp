# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from num2words import num2words
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    journal_general_ids = fields.One2many('account.journal.general', 'picking_id', 'Journal general',
                                          ondelete='cascade')
    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
        index=True, default=fields.Datetime.now, tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    x_warehouse_in_id = fields.Many2one('stock.warehouse', 'Warehouse In', compute='_compute_warehouse')
    x_warehouse_in_name = fields.Char('Warehouse In', compute='_compute_warehouse', store=True)
    x_warehouse_out_id = fields.Many2one('stock.warehouse', 'Warehouse Out', compute='_compute_warehouse')
    x_warehouse_out_name = fields.Char('Warehouse Out', compute='_compute_warehouse', store=True)
    x_check_warehouse = fields.Boolean(default=False)

    x_type_transfer = fields.Selection([('in_transfer', 'In Transfer'), ('out_transfer', 'Out Transfer')],
                                       string="Type Transfer")

    # x_location_in_name = fields.Char('Location ID', related='location_id.name')
    # x_location_out_name = fields.Char('Location Dest ID', related='location_dest_id.name')

    @api.depends('origin')
    def _compute_warehouse(self):
        for record in self:
            record.x_warehouse_in_id = None
            record.x_warehouse_out_id = None
            if record.origin:
                stock_transfer = self.env['stock.transfer'].search([('name', '=', record.origin)], limit=1)
                if stock_transfer:
                    record.x_warehouse_out_id = stock_transfer.warehouse_id.id
                    record.x_warehouse_out_name = stock_transfer.warehouse_id.name
                    record.x_warehouse_in_id = stock_transfer.warehouse_dest_id.id
                    record.x_warehouse_in_name = stock_transfer.warehouse_dest_id.name
                    record.x_check_warehouse = True

    def number_to_text(self, number):
        if number:
            amount_to_word = num2words(number, lang='vi_VN').capitalize() + " đồng chẵn."
            return amount_to_word
        else:
            return ''

    def action_assign(self):
        super().action_assign()
        if self.origin:
            stock_request = self.env['stock.request'].search([('name', '=', self.origin)], limit=1)
            if stock_request:
                stock_request_imp_line = self.env['stock.request.import.line'].search(
                    [('stock_request_id', '=', stock_request.id)])
                stock_request_imp = self.env['stock.request.import'].search(
                    [('id', '=', stock_request_imp_line.stock_request_import_id.id)])
                if stock_request_imp_line:
                    for record in stock_request_imp_line:
                        if stock_request_imp.type == 'other_output':
                            record.status = 'assigned'
        return super(StockPicking, self).action_assign()

    def do_print_picking(self):
        if self.picking_type_id.code == 'incoming' or self._context.get('transfer_incoming'):
            url = 'report/pdf/ev_stock_picking.report_template_stock_picking_in_view/%s' % (self.id)
        if self.picking_type_id.code == 'outgoing' or self._context.get('transfer_outgoing'):
            url = 'report/pdf/ev_stock_picking.report_template_stock_picking_out_view/%s' % (self.id)
        self.write({'printed': True})
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
            'res_id': self.id,
        }

    @api.depends('picking_type_id.show_operations')
    def _compute_show_operations(self):
        for picking in self:
            if picking.picking_type_id.show_operations:
                if (picking.state == 'draft' and picking.immediate_transfer) or picking.state != 'draft':
                    picking.show_operations = True
                else:
                    picking.show_operations = False
            else:
                picking.show_operations = False

    # re-define for not merge intransfer
    def action_confirm(self):
        self._check_company()
        self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
        # call `_action_confirm` on every draft move
        if self.picking_type_id.code != 'internal':
            self.mapped('move_lines') \
                .filtered(lambda move: move.state == 'draft') \
                ._action_confirm()
        else:
            self.mapped('move_lines') \
                .filtered(lambda move: move.state == 'draft') \
                ._action_confirm(merge=False)

        # run scheduler for moves forecasted to not have enough in stock
        self.mapped('move_lines').filtered(
            lambda move: move.state not in ('draft', 'cancel', 'done'))._trigger_scheduler()
        if self.origin:
            stock_request = self.env['stock.request'].search([('name', '=', self.origin)], limit=1)
            if stock_request:
                stock_request_imp_line = self.env['stock.request.import.line'].search(
                    [('stock_request_id', '=', stock_request.id)])
                stock_request_imp = self.env['stock.request.import'].search(
                    [('id', '=', stock_request_imp_line.stock_request_import_id.id)])
                if stock_request_imp_line:
                    for record in stock_request_imp_line:
                        if stock_request_imp.type == 'other_output':
                            record.status = 'wait'
        return True

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        if self.origin:
            origin = self.origin.split('/')[0]
            if origin == 'RETURN':
                self.auto_fill_quanty_done()

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(
                float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(
                float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line
                in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(
                        lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product
        # Check xuất kho âm
        try:
            if self.location_id.usage == 'internal':
                if not self.location_id.x_warehouse_id.out_minus:
                    for move_line in self.move_ids_without_package:
                        total_availability = self.env['stock.quant']._get_available_quantity(move_line.product_id,
                                                                                             self.location_id)
                        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        total_availability = float_round(total_availability, precision_digits=precision_digits,
                                                         rounding_method='HALF-UP')
                        if move_line.quantity_done > total_availability:
                            raise ValidationError(_('Not enough goods! Product "%s" is not in stock "%s":%s ') % (
                                move_line.product_id.name, self.location_id.name, total_availability))
        except Exception as e:
            raise ValidationError(e)

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(
                    products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(
                    pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _(
                    '\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(
                    pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (
                    ', '.join(pickings_without_lots.mapped('name')),
                    ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        if self.company_id.x_allow_backorder == False:
            res = self.with_context(skip_backorder=True)._pre_action_done_hook()
        else:
            res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.company_id.x_allow_backorder == False:
            self.with_context(cancel_backorder=True)._action_done()
        else:
            if self.env.context.get('picking_ids_not_to_backorder'):
                pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
                pickings_to_backorder = self - pickings_not_to_backorder
            else:
                pickings_not_to_backorder = self.env['stock.picking']
                pickings_to_backorder = self
            pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
            pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        if self.origin:
            stock_request = self.env['stock.request'].search([('name', '=', self.origin)], limit=1)
            purchase_order = self.env['purchase.order'].search([('name', '=', self.origin)], limit=1)
            if stock_request:
                stock_request_imp_line = self.env['stock.request.import.line'].search(
                    [('stock_request_id', '=', stock_request.id)])
                stock_request_imp = self.env['stock.request.import'].search(
                    [('id', '=', stock_request_imp_line.stock_request_import_id.id)])
                if stock_request_imp_line:
                    for record in stock_request_imp_line:
                        for line in self.move_line_ids_without_package:
                            if record.product_id.id == line.product_id.id:
                                record.quantity_done = line.qty_done
                                if stock_request_imp.type == 'other_input':
                                    record.state = 'done'
                                elif stock_request_imp.type == 'other_output':
                                    record.status = 'done'
            if purchase_order:
                if purchase_order.x_picking_confirm == False:
                    purchase_order.x_picking_confirm = True
                # ghi lại số lượng nhận
                supply_purchase_order_line = self.env['supply.purchase.order.line'].search(
                    [('purchase_order_id.id', '=', purchase_order.id)])
                if supply_purchase_order_line:
                    for spo_line in supply_purchase_order_line:
                        for line in self.move_line_ids_without_package:
                            if line.product_id.id == spo_line.product_id.id:
                                spo_line.qty_in = spo_line.qty_in + line.qty_done
        return True

    def unlink(self):
        raise UserError(_('You can not delete'))

    def action_assign(self):
        self.auto_fill_quanty_done()
        return super(StockPicking, self).action_assign()

    def auto_fill_quanty_done(self):
        for move_line in self.move_ids_without_package:
            if self.location_id.get_warehouse().out_minus or self.location_id.usage != 'internal':
                move_line.quantity_done = move_line.product_uom_qty
            else:
                move_line.quantity_done = move_line.reserved_availability

    def _action_done(self):
        try:
            if self.location_id.usage == 'internal':
                if not self.location_id.x_warehouse_id.out_minus:
                    for move_line in self.move_ids_without_package:
                        total_availability = self.env['stock.quant']._get_available_quantity(move_line.product_id,
                                                                                             self.location_id)
                        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        total_availability = float_round(total_availability, precision_digits=precision_digits,
                                                         rounding_method='HALF-UP')
                        if move_line.quantity_done > total_availability:
                            raise ValidationError(_('Not enough goods! Product "%s" is not in stock "%s":%s ') % (
                                move_line.product_id.name, self.location_id.name, total_availability))
        except Exception as e:
            raise ValidationError(e)

        return super(StockPicking, self)._action_done()

    def do_print_bill_picking(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.report_template_stock_picking_bill_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def do_print_picking_user(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.report_template_stock_picking_in_user_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def do_print_bill_transfer(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.report_template_stock_picking_bill_transfer_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def do_print_picking_return(self):
        # purchase_order = self.env['purchase.order'].sudo().search([('name', '=', self.origin)], limit=1)
        # purchase_order.do_print_return_products()
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_picking.report_template_stock_picking_return_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }
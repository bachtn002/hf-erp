# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm
from odoo.tools import float_is_zero
from datetime import datetime


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_description = fields.Text('Description')
    x_is_posted = fields.Boolean(string="Is Posted", default=False, copy=False)
    x_unit_cost = fields.Float(string="Unit Cost", compute='_compute_cost', store=True)
    x_value = fields.Float(string='Total cost', compute='_compute_cost', store=True)

    def action_create_account_move(self, vals):
        for stock_move in vals:
            stock_move_obj = self.search([('id','=',stock_move)], limit=1)
            if stock_move_obj:
                account_move = self.env['account.move'].search([('stock_move_id', '=', stock_move_obj.id),('state','=','posted')], limit=1)
                if not account_move:
                    stock_valuation_layers = self.env['stock.valuation.layer'].sudo()
                    stock_valuation_id = stock_valuation_layers.search([('stock_move_id','=',stock_move_obj.id)], limit =1)
                    if stock_valuation_id:
                        stock_move_obj._account_entry_move(stock_valuation_id.quantity, stock_valuation_id.description, stock_valuation_id.id, stock_valuation_id.value)
                    else:
                        valued_moves = {valued_type: self.env['stock.move'] for valued_type in self._get_valued_types()}
                        for valued_type in self._get_valued_types():
                            if getattr(stock_move_obj, '_is_%s' % valued_type)():
                                valued_moves[valued_type] |= stock_move_obj

                        # Create the valuation layers in batch by calling `moves._create_valued_type_svl`.
                        for valued_type in self._get_valued_types():
                            todo_valued_moves = valued_moves[valued_type]
                            if todo_valued_moves:
                                todo_valued_moves._sanity_check_for_valuation()
                                stock_valuation_layers |= getattr(todo_valued_moves, '_create_%s_svl' % valued_type)()

                        for svl in stock_valuation_layers:
                            if not svl.product_id.valuation == 'real_time':
                                continue
                            svl.stock_move_id._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)

    def action_create_account_move_exist_valuation(self, vals):
        for stock_move in vals:
            stock_move_obj = self.search([('id', '=', stock_move)], limit=1)
            if stock_move_obj:
                account_move = self.env['account.move'].search(
                    [('stock_move_id', '=', stock_move_obj.id), ('state', '=', 'posted')], limit=1)
                if not account_move:
                    stock_valuation_id = self.env['stock.valuation.la']


    @api.depends('quantity_done', 'product_id', 'purchase_line_id.price_unit', 'picking_id', 'state')
    def _compute_cost(self):
        for item in self:
            if item.purchase_line_id.id:
                price_unit = item.product_uom._compute_quantity(item.purchase_line_id.price_unit,
                                                                item.purchase_line_id.product_uom, rounding_method='HALF-UP')
                item.x_unit_cost = price_unit
                item.x_value = price_unit * item.quantity_done
            elif item.picking_id.id and item.picking_id.x_type_other == 'incoming':
                price_unit = item.price_unit
                item.x_unit_cost = price_unit
                item.x_value = price_unit * item.quantity_done
            elif item.picking_id and item.picking_id.picking_type_id.code == 'incoming':
                product_process_id = self.env['product.process'].search([('name','=',item.picking_id.origin)], limit=1)
                if product_process_id:
                    price_unit = item.price_unit
                    item.x_unit_cost = price_unit
                    item.x_value = price_unit * item.quantity_done
                else:
                    item.x_unit_cost = item.product_id.standard_price
                    item.x_value = item.product_id.standard_price * item.quantity_done
            else:
                # chan viec tinh gia gia tri nhap kho ck noi bo khi da tinh gia von
                if item.picking_id.id:
                    transfer_id = self.env['stock.transfer'].sudo().search([('in_picking_id', '=', item.picking_id.id)])
                    if transfer_id:
                        if transfer_id.in_picking_id.state == 'done':
                            todayDate = datetime.now()
                            date_check = todayDate.replace(day=1, hour=0, minute=0, second=0)
                            date_export = transfer_id.in_date
                            if not transfer_id.in_date:
                                date_export = item.date
                            if date_export < date_check:
                                continue
                unit_cost = abs(item._get_price_unit())
                if item.product_id.cost_method == 'standard':
                    unit_cost = item.product_id.standard_price
                    # warehouse_id = item.location_dest_id.get_warehouse() if item.location_dest_id.usage == 'internal' and item.location_dest_id.x_transit_location == False else item.location_id.get_warehouse()
                    # for price in item.product_id.product_price_ids:
                    #     if price.inventory_valuation_group_id.id == warehouse_id.x_inventory_valuation_group_id.id:
                    #         unit_cost = price.cost
                    #         break
                qty = item.quantity_done if item.location_dest_id.usage == 'internal' else -(item.quantity_done)
                item.x_unit_cost = round(unit_cost)
                item.x_value = round(unit_cost * qty)

    def _action_done(self, cancel_backorder=False):
        for item in self:
            if item._is_out():
                if item.purchase_line_id:
                    if item.purchase_line_id.order_id.id:
                        item.name = 'Phiếu xuất trả NCC ' + item.purchase_line_id.order_id.display_name
                        item.reference = item.purchase_line_id.order_id.name
                    item.x_description = 'XTNCC Xuất trả NCC'
                elif item.picking_id:
                    if item.picking_id.x_type_other == 'outgoing':
                        item.name = 'Phiếu xuất khác ' + item.picking_id.display_name
                        item.x_description = 'XK Xuất khác'
                else:
                    item.name = 'XUAT ' + item.name
                    item.x_description = 'XUAT'
            elif item._is_in():
                if item.purchase_line_id:
                    item.name = 'Phiếu nhập mua ' + item.purchase_line_id.order_id.display_name
                    item.reference = item.purchase_line_id.order_id.name
                    item.x_description = 'PNM Phiếu nhập mua'
                    # tiennq
                    x_warehouse_id = item.location_dest_id.get_warehouse()
                    if all([price.inventory_valuation_group_id.id != x_warehouse_id.x_inventory_valuation_group_id.id for price in
                            item.product_id.product_price_ids]):
                        # gia_von
                        self.env['product.price'].create({
                            'product_id': item.product_id.id,
                            'product_tmpl_id': item.product_id.product_tmpl_id.id,
                            'cost': item.purchase_line_id.price_unit,
                            'company_id': item.company_id.id,
                            'inventory_valuation_group_id': x_warehouse_id.x_inventory_valuation_group_id.id
                        })
                        # lich_su_gia_von
                        self.env['product.price.history'].create({
                            'product_id': item.product_id.id,
                            'product_tmpl_id': item.product_id.product_tmpl_id.id,
                            'datetime': fields.Date.today(),
                            'cost_price_period_line_id': False,
                            'cost': item.purchase_line_id.price_unit,
                            'company_id': item.company_id.id,
                            'inventory_valuation_group_id': x_warehouse_id.x_inventory_valuation_group_id.id
                        })
                elif item.picking_id:
                    if item.picking_id.x_type_other == 'incoming':
                        item.name = 'Phiếu nhập khác ' + item.picking_id.display_name
                        item.reference = item.picking_id.name
                        item.x_description = 'NK Nhập khác'
                        x_warehouse_id = item.location_dest_id.get_warehouse()
                        if all([price.inventory_valuation_group_id.id != x_warehouse_id.x_inventory_valuation_group_id.id for price in
                                item.product_id.product_price_ids]):
                            # gia_von
                            self.env['product.price'].create({
                                'product_id': item.product_id.id,
                                'product_tmpl_id': item.product_id.product_tmpl_id.id,
                                'cost': item.price_unit,
                                'company_id': item.company_id.id,
                                'inventory_valuation_group_id': x_warehouse_id.x_inventory_valuation_group_id.id
                            })
                            # lich_su_gia_von
                            self.env['product.price.history'].create({
                                'product_id': item.product_id.id,
                                'product_tmpl_id': item.product_id.product_tmpl_id.id,
                                'datetime': fields.Date.today(),
                                'cost_price_period_line_id': False,
                                'cost': item.price_unit,
                                'company_id': item.company_id.id,
                                'inventory_valuation_group_id': x_warehouse_id.x_inventory_valuation_group_id.id
                            })
                else:
                    item.name = 'NHAP ' + item.name
                    item.x_description = 'NHAP'
            else:
                item.name = 'Phiếu điều chuyển nội bộ ' + item.name
                item.x_description = 'DCNB Điều chuyển nội bộ'
                transfer_id = self.env['stock.transfer'].search([('out_picking_id', '=', item.picking_id.id)], limit=1)
                if transfer_id:
                    warehouse_id = transfer_id.warehouse_id
                    unit_cost = 0
                    for price in item.product_id.product_price_ids:
                        if price.inventory_valuation_group_id.id == warehouse_id.x_inventory_valuation_group_id.id:
                            unit_cost = price.cost
                            break
                    x_warehouse_id = transfer_id.warehouse_dest_id
                    if all([price.inventory_valuation_group_id.id != x_warehouse_id.x_inventory_valuation_group_id.id for price in
                            item.product_id.product_price_ids]):
                        # gia_von
                        self.env['product.price'].create({
                            'product_id': item.product_id.id,
                            'product_tmpl_id': item.product_id.product_tmpl_id.id,
                            'cost': unit_cost,
                            'company_id': item.company_id.id,
                            'inventory_valuation_group_id': x_warehouse_id.x_inventory_valuation_group_id.id
                        })
                        # lich_su_gia_von
                        self.env['product.price.history'].create({
                            'product_id': item.product_id.id,
                            'product_tmpl_id': item.product_id.product_tmpl_id.id,
                            'datetime': fields.Date.today(),
                            'cost_price_period_line_id': False,
                            'cost': unit_cost,
                            'company_id': item.company_id.id,
                            'inventory_valuation_group_id': x_warehouse_id.x_inventory_valuation_group_id.id
                        })
            item._compute_cost()
        return super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)
        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if self.picking_id:
            description = self.picking_id.name
        location_id = location_dest_id = False
        if self._is_out():
            location_id = location_dest_id = self.location_id.id
        elif self._is_in():
            location_id = location_dest_id = self.location_dest_id.id
        # elif self._is_internal():
        #     if self.location_id.usage == 'internal' and self.location_dest_id.usage == 'internal':
        #         location_id = self.location_id.id
        #         location_dest_id = self.location_dest_id.id
        #     else:
        #         location_id = location_dest_id = self.location_id.id if self.location_id.usage == 'internal' else self.location_dest_id.id
        #location_check = False
        if move_lines:
            for line in move_lines:
                if self._is_out():
                    line[2].update({
                        'x_location_id': location_id,
                        'x_type_transfer': 'out',
                    })
                elif self._is_in():
                    line[2].update({
                        'x_location_id': location_dest_id,
                        'x_type_transfer': 'in',
                    })
                # elif self._is_internal():
                #     if self.location_id.usage == 'internal' and self.location_dest_id.usage == 'internal':
                #         if line[2]['credit'] > 0:
                #             line[2].update({
                #                 'x_location_id': location_id,
                #                 'x_type_transfer': 'out',
                #             })
                #         elif line[2]['debit'] > 0:
                #             line[2].update({
                #                 'x_location_id': location_dest_id,
                #                 'x_type_transfer': 'in',
                #             })
                #         else:
                #             line[2].update({
                #                 'x_location_id': False,
                #             })
                #             if line[2]['x_location_id']:
                #                 location_check = line[2]['x_location_id']
                #                 continue
                #             if not location_check:
                #                 line[2].update({
                #                     'x_location_id': location_id,
                #                     'x_type_transfer': 'out',
                #                 })
                #                 location_check = True
                #             else:
                #                 line[2].update({
                #                     'x_location_id': location_dest_id,
                #                     'x_type_transfer': 'in',
                #                 })
                #
                #     else:
                #         if self.location_id.usage == 'internal':
                #             line[2].update({
                #                 'x_location_id': location_id,
                #                 'x_type_transfer': 'out',
                #             })
                #         if self.location_dest_id.usage == 'internal':
                #             line[2].update({
                #                 'x_location_id': location_dest_id,
                #                 'x_type_transfer': 'in',
                #             })
                line[2].update({
                    'ref': description,
                })
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()

    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        acc_valuation = False
        if self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
            if self.location_id.usage == 'internal':
                acc_valuation = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id

        if self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
            if self.location_dest_id.usage == 'internal':
                acc_valuation = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id

        if self.location_id.usage == 'internal' and self.location_dest_id.usage == 'internal':
            acc_src = acc_dest = accounts_data['stock_valuation'].id
        if not acc_valuation:
            acc_valuation = accounts_data.get('stock_valuation', False)
            if acc_valuation:
                acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(
                _('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
        if not acc_src:
            raise UserError(_(
                'Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (
                                self.product_id.display_name))
        if not acc_dest:
            raise UserError(_(
                'Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (
                                self.product_id.display_name))
        if not acc_valuation:
            raise UserError(_(
                'You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation

    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False
        # tiennq
        if len(self.account_move_ids.filtered(lambda r: r.state == 'posted')):
            return False

        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_from and location_from.usage == 'customer':  # goods returned from customer
                self.with_company(company_to)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)
            # tiennq
            elif location_from and location_from.usage == 'inventory':  # goods inventory
                self.with_company(company_to)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)
            elif location_from and location_from.usage == 'production':
                self.with_company(company_to)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)
            else:
                #TODO
                pass
                # self.with_company(company_to)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = -1 * cost
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_to and location_to.usage == 'supplier':  # goods returned to supplier
                pass
                # self.with_company(company_from)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost)
                # tiennq
            # elif location_to and location_to.usage == 'inventory':  # goods inventory
            #     self.with_company(company_from)._create_account_move_line(acc_src, acc_dest, journal_id, qty, description, svl_id, cost)
            else:
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if self._is_dropshipped():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id,
                                                                                 cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id,
                                                                                 cost)
            elif self._is_dropshipped_returned():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id,
                                                                                 cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty, description, svl_id,
                                                                                 cost)

        if self.company_id.anglo_saxon_accounting:
            # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            self._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=self.product_id)

        # new code
        warehouse_id = self.location_id.get_warehouse()
        warehouse_dest_id = self.location_dest_id.get_warehouse()
        x_warehouse_id = False
        # if self._is_internal():
        #     x_inventory_valuation_group_id = False
        #     x_inventory_valuation_group_dest_id = False
        #     if warehouse_id.x_inventory_valuation_group_id:
        #         x_inventory_valuation_group_id = warehouse_id.x_inventory_valuation_group_id
        #     if warehouse_dest_id.x_inventory_valuation_group_id:
        #         x_inventory_valuation_group_dest_id = warehouse_dest_id.x_inventory_valuation_group_id
        #     if x_inventory_valuation_group_id and x_inventory_valuation_group_dest_id:
        #         if x_inventory_valuation_group_id.id != x_inventory_valuation_group_dest_id.id:
        #             raise UserError(_('Không thể tạo dịch chuyển giữa 2 địa điểm khác kho!'))
        #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        #         self.with_context(force_company=self.company_id.id, force_create_move=True)._create_account_move_line(acc_valuation, acc_valuation,
        #                                                                                                               journal_id, qty,
        #                                                                                                               description, svl_id, cost)
        #         x_warehouse_id = warehouse_id.id
        #     elif x_inventory_valuation_group_id and x_inventory_valuation_group_dest_id == False:
        #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        #         self.with_context(force_company=self.company_id.id, force_create_move=True)._create_account_move_line(acc_dest, acc_valuation,
        #                                                                                                               journal_id, qty,
        #                                                                                                               description, svl_id, cost)
        #         x_warehouse_id = warehouse_id.id
        #     elif x_inventory_valuation_group_id == False and x_inventory_valuation_group_dest_id:
        #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        #         self.with_context(force_company=self.company_id.id, force_create_move=True)._create_account_move_line(acc_src, acc_valuation,
        #                                                                                                               journal_id, qty,
        #                                                                                                               description, svl_id, cost)
        #         x_warehouse_id = warehouse_dest_id.id

        if self._is_out():
            x_warehouse_id = warehouse_id.id
        elif self._is_in():
            x_warehouse_id = warehouse_dest_id.id
        for move_id in self.account_move_ids.filtered(lambda r: r.state == 'posted'):
            for move_line_id in move_id.line_ids:
                move_line_id.x_warehouse_id = x_warehouse_id

    # def _get_internal_move_lines(self):
    #     """ Returns the `stock.move.line` records of `self` considered as outgoing. It is done thanks
    #     to the `_should_be_valued` method of their source and destionation location as well as their
    #     owner.
    #
    #     :returns: a subset of `self` containing the outgoing records
    #     :rtype: recordset
    #     """
    #     res = self.env['stock.move.line']
    #     for move_line in self.move_line_ids:
    #         if move_line.owner_id and move_line.owner_id != move_line.company_id.partner_id:
    #             continue
    #         if move_line.location_id.usage in ('internal', 'transit') and move_line.location_dest_id.usage in ('internal', 'transit'):
    #             res |= move_line
    #     return res
    #
    # def _is_internal(self):
    #     """Check if the move should be considered as leaving the company so that the cost method
    #     will be able to apply the correct logic.
    #
    #     :returns: True if the move is leaving the company else False
    #     :rtype: bool
    #     """
    #     self.ensure_one()
    #     if self._get_internal_move_lines():
    #         return True
    #     return False

    # def _create_internal_svl(self, forced_quantity=None):
    #     """Create a `stock.valuation.layer` from `self`.
    #
    #     :param forced_quantity: under some circunstances, the quantity to value is different than
    #         the initial demand of the move (Default value = None)
    #     """
    #     svl_vals_list = []
    #     for move in self:
    #         unit_cost = move.x_unit_cost
    #         quantity = move.product_qty if move.location_dest_id.usage == 'internal' else - move.product_qty
    #         svl_vals = move.product_id._prepare_internal_svl_vals(quantity, unit_cost)
    #         svl_vals.update(move._prepare_common_svl_vals())
    #         if forced_quantity:
    #             svl_vals[
    #                 'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
    #         svl_vals_list.append(svl_vals)
    #     return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
            unit_cost = move.x_unit_cost
            svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_out_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
            if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
                continue
            x_warehouse_id = move.location_id.get_warehouse()
            svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
            svl_vals.update(move._prepare_common_svl_vals())
            unit_cost = move.x_unit_cost
            svl_vals.update({
                'unit_cost': unit_cost,
                'value': unit_cost * -1 * (forced_quantity or valued_quantity),
            })
            if forced_quantity:
                svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_dropshipped_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move.move_line_ids
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
            quantity = forced_quantity or valued_quantity
            unit_cost = move.x_unit_cost
            common_vals = dict(move._prepare_common_svl_vals(), remaining_qty=0)

            # create the in
            in_vals = {
                'unit_cost': unit_cost,
                'value': unit_cost * quantity,
                'quantity': quantity,
            }
            in_vals.update(common_vals)
            svl_vals_list.append(in_vals)

            # create the out
            out_vals = {
                'unit_cost': unit_cost,
                'value': unit_cost * quantity * -1,
                'quantity': quantity * -1,
            }
            out_vals.update(common_vals)
            svl_vals_list.append(out_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    # @api.model
    # def _get_valued_types(self):
    #     vals = super(StockMove, self)._get_valued_types()
    #     vals.append('internal')
    #     return vals

    def _prepare_account_move_line_from_move(self, move):
        res = super(StockMove, self)._prepare_account_move_line_from_move(move)
        if self.purchase_line_id:
            res.update({
                'x_warehouse_id': self.purchase_line_id.order_id.picking_type_id.warehouse_id.id
            })
        return res

# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.exceptions import UserError, except_orm, ValidationError
from dateutil.relativedelta import relativedelta
from itertools import groupby
from odoo.tools.misc import formatLang
from odoo.osv import expression


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_is_return = fields.Boolean('Is return products', default=False)

    x_invoice_confirm_diff = fields.Boolean('Invoice Differrence Purchase', default=False)

    partner_ref = fields.Char('Vendor Reference', copy=False, compute='_compute_partner_ref',
                              help="Reference of the sales order or bid sent by the vendor. "
                                   "It's used to do the matching when you receive the "
                                   "products as this reference is usually written on the "
                                   "delivery order sent by your vendor.")
    x_picking_confirm = fields.Boolean('Picking Confirm', default=False, copy=False)

    @api.depends('state', 'order_line.qty_to_invoice')
    def _get_invoiced(self):
        try:
            super(PurchaseOrder, self)._get_invoiced()
            for order in self:
                if order.x_invoice_confirm_diff == True:
                    order.invoice_status = 'invoiced'
        except Exception as e:
            raise ValidationError(e)

    @api.depends('partner_id')
    def _compute_partner_ref(self):
        for record in self:
            record.partner_ref = record.partner_id.name
            if record.partner_id.ref:
                record.partner_ref = record.partner_id.ref

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', ('name', operator, name), ('partner_ref', operator, name),
                      ('partner_id.id', operator, name), ('partner_id.name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.depends('name', 'partner_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name + po.partner_id.name
            if po.partner_ref:
                name = po.name + ' [' + str(po.partner_id.ref) + ']' + po.partner_id.name
            if self.env.context.get('show_total_amount') and po.amount_total:
                name += ': ' + formatLang(self.env, po.amount_total, currency_obj=po.currency_id)
            result.append((po.id, name))
        return result

    @api.model
    def create(self, vals_list):
        res = super(PurchaseOrder, self).create(vals_list)
        if res.x_is_return:
            res.name = 'RETURN/' + res.name
        return res

    @api.model
    def _get_picking_type(self, company_id):
        if not self.env.context.get('default_x_is_return', False):
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id.code', '=', 'VN0402'),
                 ('warehouse_id.company_id', '=', company_id)])
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
                if not picking_type:
                    picking_type = self.env['stock.picking.type'].search(
                        [('code', '=', 'incoming'), ('warehouse_id', '=', False)])
            return picking_type[:1]
        else:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing'), ('warehouse_id.code', '=', 'VN0405'),
                 ('warehouse_id.company_id', '=', company_id)])
            if not picking_type:
                picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)])
                if not picking_type:
                    picking_type = self.env['stock.picking.type'].search(
                        [('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
            return picking_type[:1]

    def _get_destination_location(self):
        self.ensure_one()
        if not self.x_is_return:
            if self.dest_address_id:
                return self.dest_address_id.property_stock_customer.id
            return self.picking_type_id.default_location_dest_id.id
        else:
            return self.picking_type_id.default_location_src_id.id

    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        location_dest_id = self._get_destination_location()
        location_id = self.partner_id.property_stock_supplier.id
        if self.x_is_return:
            location_dest_id = self.partner_id.property_stock_supplier.id
            location_id = self._get_destination_location()
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id,
            'create_date': datetime.now()
        }

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        if self.x_is_return:
            move_type = self._context.get('default_move_type', 'in_refund')
        else:
            move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (
                    self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))
        if self.x_is_return:
            journal_id = self.env['account.journal'].search([('type', '=', 'purchase'), ('code', '=', 'RHD')], limit=1)
            if not journal_id:
                raise UserError(
                    _('You need to configure the vendor return invoice journal.'))
        else:
            journal_id = self.env['account.journal'].search([('type', '=', 'purchase'), ('code', '!=', 'RHD')], limit=1)
            if not journal_id:
                raise UserError(
                    _('You need to configure the vendor invoice journal.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (
                x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                'journal_id': journal_id.id,
                'x_picking_type_id': self.picking_type_id.id
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        if self.x_is_return:
            AccountMove = self.env['account.move'].with_context(default_move_type='in_refund')
        else:
            AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(
            lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        if self.x_is_return:
            result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_refund_type')
        else:
            result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    def button_cancel(self):
        for order in self:
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(
                        _("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

        for picking in self.picking_ids:
            picking.action_cancel()
        self.write({'state': 'cancel'})

    def button_confirm(self):
        return super(PurchaseOrder, self).button_confirm()

    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(
                    picking) if not order.x_is_return else order.order_line._create_stock_moves_return(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return True

    def do_print_return_products(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/ev_stock_return_products.report_template_stock_return_products_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_return_qty = fields.Float(string='Quantity return', digits='Product Unit of Measure', required=True,
                                      default=0)
    qty_returned = fields.Float("Returned Qty", compute='_compute_qty_returned', inverse='_inverse_qty_returned',
                                compute_sudo=True, store=True, digits='Product Unit of Measure')

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom', 'qty_received_method',
                 'qty_received_manual')
    def _compute_qty_returned(self):
        for line in self:
            if line.qty_received_method == 'manual':
                line.qty_returned = line.qty_received_manual or 0.0
            else:
                line.qty_returned = 0.0
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line.move_ids.filtered(lambda m: m.product_id == line.product_id):
                    if move.state == 'done':
                        if move.location_id.usage == "supplier":
                            if move.to_refund:
                                total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif (
                                move.location_dest_id.usage == "internal"
                                and move.to_refund
                                and move.location_dest_id
                                not in self.env["stock.location"].search(
                            [("id", "child_of", move.warehouse_id.view_location_id.id)]
                        )
                        ):
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                line.qty_returned = total

    @api.onchange('qty_returned')
    def _inverse_qty_returned(self):
        """ When writing on qty_received, if the value should be modify manually (`qty_received_method` = 'manual' only),
            then we put the value in `qty_received_manual`. Otherwise, `qty_received_manual` should be False since the
            received qty is automatically compute by other mecanisms.
        """
        for line in self:
            if line.qty_received_method == 'manual':
                line.qty_received_manual = line.qty_received
            else:
                line.qty_received_manual = 0.0

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            product_qty = vals['product_qty']
            if line.order_id.x_is_return:
                product_qty = line.product_return_qty
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                product_qty,
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.constrains('product_return_qty', 'order_id')
    def _constrain_product_return_qty(self):
        for item in self:
            if item.order_id and item.order_id.x_is_return:
                if item.product_return_qty <= 0:
                    raise except_orm('Warning!', _('Quantity return is must be greater than 0.'))

    @api.onchange('product_qty', 'product_uom', 'product_return_qty')
    def _onchange_quantity(self):
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        product_qty = self.product_qty
        if self.product_return_qty:
            product_qty = self.product_return_qty
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        # If not seller, use the standard price. It needs a proper currency conversion.
        if not seller:
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                self.product_id.uom_id._compute_price(self.product_id.standard_price, self.product_id.uom_po_id),
                self.product_id.supplier_taxes_id,
                self.taxes_id,
                self.company_id,
            )
            if price_unit and self.order_id.currency_id and self.order_id.company_id.currency_id != self.order_id.currency_id:
                price_unit = self.order_id.company_id.currency_id._convert(
                    price_unit,
                    self.order_id.currency_id,
                    self.order_id.company_id,
                    self.date_order or fields.Date.today(),
                )
            self.price_unit = price_unit
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                             self.product_id.supplier_taxes_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        self.ensure_one()
        product = self.product_id.with_context(lang=self.order_id.dest_address_id.lang or self.env.user.lang)
        description_picking = product._get_description(self.order_id.picking_type_id)
        if self.product_description_variants:
            description_picking += "\n" + self.product_description_variants
        date_planned = self.date_planned or self.order_id.date_planned
        location_id = self.order_id.partner_id.property_stock_supplier.id
        location_dest_id = (self.orderpoint_id and not (
                self.move_ids | self.move_dest_ids)) and self.orderpoint_id.location_id.id or self.order_id._get_destination_location()
        if self.order_id.x_is_return:
            # product_uom_qty = self.product_return_qty
            location_id = (self.orderpoint_id and not (
                    self.move_ids | self.move_dest_ids)) and self.orderpoint_id.location_id.id or self.order_id._get_destination_location()
            location_dest_id = self.order_id.partner_id.property_stock_supplier.id
        return {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'date': date_planned,
            'date_deadline': date_planned + relativedelta(days=self.order_id.company_id.po_lead),
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'description_picking': description_picking,
            'propagate_cancel': self.propagate_cancel,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
        }

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty',
                 'order_id.state', 'qty_returned')
    def _compute_qty_invoiced(self):
        for line in self:
            # compute qty_invoiced
            if line.order_id.x_is_return:
                qty_return_invoiced = 0.0
                for inv_line in line.invoice_lines:
                    if inv_line.move_id.state not in ['cancel']:
                        qty_return_invoiced += inv_line.product_uom_id._compute_quantity(inv_line.quantity,
                                                                                         line.product_uom)
                line.qty_invoiced = qty_return_invoiced
                # compute qty_to_invoice
                if line.order_id.state in ['purchase', 'done']:
                    if line.product_id.purchase_method == 'purchase':
                        line.qty_to_invoice = line.product_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_returned - line.qty_invoiced
                else:
                    line.qty_to_invoice = 0
            else:
                # compute qty_invoiced
                qty = 0.0
                for inv_line in line.invoice_lines:
                    if inv_line.move_id.state not in ['cancel']:
                        if inv_line.move_id.move_type == 'in_invoice':
                            qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                        elif inv_line.move_id.move_type == 'in_refund':
                            qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
                line.qty_invoiced = qty

                # compute qty_to_invoice
                if line.order_id.state in ['purchase', 'done']:
                    if line.product_id.purchase_method == 'purchase':
                        line.qty_to_invoice = line.product_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_received - line.qty_invoiced
                else:
                    line.qty_to_invoice = 0

    def _prepare_stock_moves_return(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res

        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        for move in incoming_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')

        move_dests = self.move_dest_ids
        if not move_dests:
            move_dests = self.move_ids.move_dest_ids.filtered(
                lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier')

        if not move_dests:
            qty_to_attach = 0
            qty_to_push = self.product_return_qty - qty
        else:
            move_dests_initial_demand = self.product_id.uom_id._compute_quantity(
                sum(move_dests.filtered(
                    lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier').mapped(
                    'product_qty')),
                self.product_uom, rounding_method='HALF-UP')
            qty_to_attach = move_dests_initial_demand - qty
            qty_to_push = self.product_return_qty - move_dests_initial_demand

        if float_compare(qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_attach,
                                                                                   self.product_id.uom_id)
            res.append(self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom))
        if float_compare(qty_to_push, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_push, self.product_id.uom_id)
            extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
            extra_move_vals['move_dest_ids'] = False  # don't attach
            res.append(extra_move_vals)
        return res

    def _create_stock_moves_return(self, picking):
        values = []
        for line in self.filtered(lambda l: not l.display_type):
            for val in line._prepare_stock_moves_return(picking):
                values.append(val)
            line.move_dest_ids.created_purchase_line_id = False

        return self.env['stock.move'].create(values)

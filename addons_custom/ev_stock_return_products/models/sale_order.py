# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        res = super(SaleOrder, self)._default_warehouse_id(self)
        company = self.env.company.id
        warehouse_ids = self.env['stock.warehouse'].sudo().search([('code', '=', 'VN0401'), ('company_id', '=', company)], limit=1)
        if not warehouse_ids:
            return res
        return warehouse_ids

    x_is_return = fields.Boolean('Is return products', default=False)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            warehouse_id = self.env['stock.warehouse'].sudo().search([('code', '=', 'VN0401'), ('company_id', '=', self.company_id.id)],
                                                                      limit=1)
            if warehouse_id.id:
                self.warehouse_id = warehouse_id.id
            else:
                self.warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)

    @api.model
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        if res.x_is_return:
            res.name = 'RETURN/' + res.name
        return res

    def action_confirm(self):
        if self.x_is_return:
            for line in self.order_line:
                line.product_uom_qty = -(line.product_return_qty)
        res = super(SaleOrder, self).action_confirm()
        if self.x_is_return:
            self._create_picking_return()
        return res

    def _prepare_procurement_group_vals_return(self):
        return {
            'name': self.name,
            'move_type': self.picking_policy,
            'sale_id': self.id,
            'partner_id': self.partner_shipping_id.id,
        }

    def _get_destination_location_return(self):
        self.ensure_one()
        picking_type_id = self.warehouse_id.in_type_id
        location_dest_id = picking_type_id.default_location_dest_id
        return [picking_type_id.id, location_dest_id.id]

    @api.model
    def _prepare_picking_return(self):
        if not self.procurement_group_id:
            group_id = self.env['procurement.group'].create(self._prepare_procurement_group_vals_return())
            self.procurement_group_id = group_id.id
        if not self.partner_id.property_stock_customer.id:
            raise UserError(_("You must set a Customer Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self._get_destination_location_return()[0],
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location_return()[1],
            'location_id': self.partner_id.property_stock_customer.id,
            'company_id': self.company_id.id,
            'sale_id': self.id,
        }

    def _create_picking_return(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking_return()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves_return(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_return_qty = fields.Float(string='Quantity return', digits='Product Unit of Measure', required=True, default=0)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'product_return_qty')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            product_uom_qty = line.product_uom_qty
            if line.order_id.x_is_return:
                product_uom_qty = line.product_return_qty

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, product_uom_qty, product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
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

    # @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    # def _get_to_invoice_qty(self):
    #     """
    #     Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
    #     calculated from the ordered quantity. Otherwise, the quantity delivered is used.
    #     """
    #     for line in self:
    #         if not line.order_id.x_is_return:
    #             if line.order_id.state in ['sale', 'done']:
    #                 if line.product_id.invoice_policy == 'order':
    #                     line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
    #                 else:
    #                     line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
    #             else:
    #                 line.qty_to_invoice = 0
    #         else:
    #             if line.order_id.state in ['sale', 'done']:
    #                 if line.product_id.invoice_policy == 'order':
    #                     line.qty_to_invoice = abs(line.product_uom_qty - line.qty_invoiced)
    #                 else:
    #                     line.qty_to_invoice = abs(line.qty_delivered + line.qty_invoiced)
    #             else:
    #                 line.qty_to_invoice = 0

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not line.order_id.x_is_return:
                if line.state not in ('sale', 'done'):
                    line.invoice_status = 'no'
                elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    line.invoice_status = 'to invoice'
                elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                        float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                    line.invoice_status = 'upselling'
                elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                    line.invoice_status = 'invoiced'
                else:
                    line.invoice_status = 'no'
            else:
                if line.state not in ('sale', 'done'):
                    line.invoice_status = 'no'
                elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    line.invoice_status = 'to invoice'
                elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                        float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                    line.invoice_status = 'upselling'
                elif float_compare(line.qty_invoiced, abs(line.product_uom_qty), precision_digits=precision) >= 0:
                    line.invoice_status = 'invoiced'
                else:
                    line.invoice_status = 'no'

    def _prepare_stock_moves_return(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self.price_unit
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and x.location_id.usage == "customer"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'location_id': self.order_id.partner_id.property_stock_customer.id,
            'location_dest_id': self.order_id._get_destination_location_return()[1],
            'picking_id': picking.id,
            'partner_id': self.order_id.partner_id.id,
            'state': 'draft',
            'sale_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id._get_destination_location_return()[0],
            'group_id': self.order_id.procurement_group_id.id,
            'origin': self.order_id.name,
            'route_ids': self.order_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.warehouse_id.id,
            'to_refund': True,
        }
        diff_quantity = self.product_return_qty - qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            so_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = so_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
            res.append(template)
        return res

    def _create_stock_moves_return(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves_return(picking):
                values.append(val)
        return self.env['stock.move'].create(values)

    def _get_computed_account_return(self):
        self.ensure_one()

        if not self.product_id:
            return

        fiscal_position = self.move_id.fiscal_position_id
        accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        if self.move_id.is_sale_document(include_receipts=True):
            # Out invoice.
            if self.move_id.type == 'out_invoice':
                return accounts['income']
            else:
                return accounts['customer_return_account'] if accounts['customer_return_account'] else accounts['income']
        elif self.move_id.is_purchase_document(include_receipts=True):
            # In invoice.
            if self.move_id.type == 'in_invoice':
                return accounts['expense']
            else:
                return accounts['return_vendor_account'] if accounts['return_vendor_account'] else accounts['expense']

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        if not self.order_id.x_is_return:
            return res
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        account_id = accounts['customer_return_account'] if accounts['customer_return_account'] else accounts['income']
        res.update({'account_id': account_id})
        return res

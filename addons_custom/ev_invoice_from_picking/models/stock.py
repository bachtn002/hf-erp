# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError
from datetime import datetime

journal_type_dict = {
    ('outgoing', 'customer'): ['out_invoice'],
    ('incoming', 'supplier'): ['in_invoice'],
}

invoice_type_dict = {
    'out_invoice': 'outgoing',
    'out_refund': 'incoming',
    'in_invoice': 'incoming',
    'in_refund': 'outgoing',
}


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('invoice_ids', 'invoice_ids.state')
    def _get_len_invoice_ids(self):
        for picking in self:
            picking.invoice_ids_count = len(picking.invoice_ids.filtered(lambda x: x.state != 'cancel'))
            if len(picking.invoice_ids.filtered(lambda x: x.state != 'cancel')) != 0:
                picking.invoice_status = 'invoiced'
            else:
                picking.invoice_status = 'no'

    invoice_ids = fields.Many2many('account.move', 'table_account_invoice_stock_picking_relation', 'picking_id',
                                   'invoice_id',
                                   string="Invoice", copy=False)
    invoice_ids_count = fields.Integer(string="Invoices", compute="_get_len_invoice_ids", store=True)
    invoice_status = fields.Selection([('no', 'Nothing to Bill'), ('invoiced', 'Billed')], string='Invoice Status',
                                      compute="_get_len_invoice_ids", store=True)

    def _prepare_invoice(self):
        self.ensure_one()
        context = self.env.context
        ref = ''
        if self.purchase_id:
            ref = self.purchase_id.name
        invoice_vals = {
            'move_type': context.get('invoice_type'),
            'partner_id': self.partner_id.id,
            'ref': ref,
            'journal_id': context.get('journal_id'),
            'company_id': self.company_id.id,
            'invoice_date': context.get('invoice_date'),
            'stock_picking_ids': [(4, self.id)],
            'user_id': context.get('user_id'),
            'invoice_origin': self.name,
            'currency_id': context.get('currency_id')
        }
        return invoice_vals

    def view_account_invoices(self):
        if self.invoice_ids:
            self.ensure_one()
            form_view_name = "account.view_move_form"
            invoice_type = self.invoice_ids[0].move_type
            if invoice_type == 'in_invoice':
                action = self.env.ref('account.action_move_in_invoice_type').sudo()
            else:  # invoice_type == 'out_invoice':
                action = self.env.ref('account.action_move_out_invoice_type').sudo()
            result = action.read()[0]
            if len(self.invoice_ids) > 1:
                result["domain"] = "[('id', 'in', %s)]" % self.invoice_ids.ids
            else:
                form_view = self.env.ref(form_view_name)
                result["views"] = [(form_view.id, "form")]
                result["res_id"] = self.invoice_ids.id
            return result

    # auto create_invoice
    # def _action_done(self):
    #     res = super(StockPicking, self)._action_done()
    #
    #     # prepare data
    #     if self.picking_type_id.code not in ['incoming', 'outgoing']:
    #         return res
    #
    #     if self.picking_type_id.sequence_code in ['IN_OTHER', 'OUT_OTHER']:
    #         return res
    #
    #     # POS
    #     if not self.sale_id and not self.purchase_id:
    #         return res
    #
    #     invoice_date = self._compute_invoice_date()
    #     invoice_payment_term_id = invoice_incoterm_id = None
    #
    #     if self.purchase_id:
    #         journal_id = self.env['account.journal'].search([('type', '=', 'purchase'),('company_id','=', self.company_id.id)], limit=1)
    #         if self.picking_type_id.code == 'incoming':
    #             invoice_type = 'in_invoice'
    #         else:
    #             invoice_type = 'in_refund'
    #         invoice_payment_term_id = self.purchase_id.payment_term_id.id if self.purchase_id.payment_term_id else None
    #         invoice_incoterm_id = self.purchase_id.incoterm_id.id if self.purchase_id.incoterm_id else None
    #
    #     if self.sale_id:
    #         journal_id = self.env['account.journal'].search([('type', '=', 'sale'),('company_id','=', self.company_id.id)], limit=1)
    #         if self.picking_type_id.code == 'incoming':
    #             invoice_type = 'out_refund'
    #         else:
    #             invoice_type = 'out_invoice'
    #
    #         invoice_payment_term_id = self.sale_id.payment_term_id.id if self.sale_id.payment_term_id else None
    #         invoice_incoterm_id = self.sale_id.incoterm.id if self.sale_id.incoterm else None
    #
    #     group_by_partner = True
    #
    #     # create invoice
    #     picking_ids = self
    #     if any([not picking.partner_id for picking in picking_ids]):
    #         raise ValidationError(_("Partner not found. For create invoice, into picking must have the partner."))
    #     picking_code_lst = picking_ids.mapped('picking_type_code')
    #     if 'internal' in picking_code_lst:
    #         raise ValidationError(_("Select only Delivery Orders / Receipts for create Invoice."))
    #     if len(set(picking_code_lst)) > 1:
    #         raise ValidationError(_("Selected picking must have same Operation Type."))
    #     if not journal_id:
    #         raise ValidationError(_('Please define an accounting sales journal for this company.'))
    #
    #     # if any([picking.state not in ['done'] for picking in picking_ids]):
    #     #     raise ValidationError(_("Selected picking must have in Done State."))
    #     groupby_lst = {}
    #     for picking_id in picking_ids:
    #         # if picking_id.invoice_ids.filtered(lambda x: x.state != 'cancel') or not picking_id.move_lines:
    #         #     continue
    #         if group_by_partner:
    #             key = picking_id.partner_id.id
    #         else:
    #             key = picking_id.id
    #         groupby_lst.setdefault(key, [])
    #         groupby_lst[key].append(picking_id)
    #     new_invoices = self.env['account.move']
    #     for lst_items in groupby_lst.values():
    #         invoice_lst = {}
    #         for picking in lst_items:
    #             user_id = False
    #             currency_id = self.env.user.company_id.currency_id.id
    #             if picking.sale_id:
    #                 user_id = picking.sale_id.user_id.id or False
    #                 currency_id = picking.sale_id.pricelist_id.currency_id.id or picking.sale_id.company_id.currency_id.id
    #             if picking.purchase_id:
    #                 user_id = picking.purchase_id.user_id.id or False
    #                 currency_id = picking.purchase_id.currency_id.id or picking.purchase_id.company_id.currency_id.id
    #             key = (picking.partner_id.id, picking.company_id.id)
    #             invoice_vals = picking.with_context(journal_id=journal_id.id, invoice_date=invoice_date,
    #                                                 invoice_type=invoice_type, user_id=user_id,
    #                                                 currency_id=currency_id,
    #                                                 date=invoice_date or datetime.now().today().date())._prepare_invoice()
    #             invoice_vals.update({
    #                 'invoice_payment_term_id': invoice_payment_term_id,
    #                 'invoice_incoterm_id': invoice_incoterm_id
    #             })
    #             if key not in invoice_lst:
    #                 invoice_vals.update({'date': invoice_date or datetime.now().today().date()})
    #                 invoice_id = self.env['account.move'].with_context(default_type=invoice_type,
    #                                                                    default_currency_id=currency_id).create(
    #                     invoice_vals)
    #                 invoice_lst[key] = invoice_id
    #                 new_invoices += invoice_id
    #             else:
    #                 invoice_id = invoice_lst[key]
    #                 update_inv_data = {'stock_picking_ids': [(4, picking.id)]}
    #                 if not invoice_id.invoice_origin or invoice_vals['invoice_origin'] \
    #                         not in invoice_id.invoice_origin.split(', '):
    #                     invoice_origin = filter(None, [invoice_id.invoice_origin, invoice_vals['invoice_origin']])
    #                     update_inv_data['invoice_origin'] = ', '.join(invoice_origin)
    #                 if invoice_vals.get('name', False) and (
    #                         not invoice_id.name or invoice_vals['name'] not in invoice_id.name.split(', ')):
    #                     invoice_name = filter(None, [invoice_id.name, invoice_vals['name']])
    #                     update_inv_data['name'] = ', '.join(invoice_name)
    #                 if update_inv_data:
    #                     invoice_id.write(update_inv_data)
    #             if invoice_id:
    #                 inv_line_vals = []
    #                 for each in picking.move_lines:
    #                     # sale invoice
    #                     if each.sale_line_id and each.sale_line_id.qty_to_invoice > 0:
    #                         qty = each.sale_line_id.qty_to_invoice
    #                         quantity_done = each.product_uom._compute_quantity(each.quantity_done,
    #                                                                            each.sale_line_id.product_uom,
    #                                                                            rounding_method="HALF-UP")
    #                         if qty > quantity_done:
    #                             qty = quantity_done
    #                         if qty > 0:
    #                             prepare_invoice_line_vals = each.sale_line_id._prepare_invoice_line()
    #                             prepare_invoice_line_vals.update({
    #                                 'quantity': qty,
    #                             })
    #                             inv_line_vals.append((0, 0, prepare_invoice_line_vals))
    #                     # purchase invoice
    #                     if each.purchase_line_id:
    #                         qty = each.purchase_line_id.product_qty - each.purchase_line_id.qty_invoiced
    #                         if not self._context.get('cancel_backorder') and 'cancel_backorder' in self._context:
    #                             quantity_done = each.product_uom._compute_quantity(each.product_uom_qty,
    #                                                                                each.purchase_line_id.product_uom,
    #                                                                                rounding_method="HALF-UP")
    #                         else:
    #                             quantity_done = each.product_uom._compute_quantity(each.quantity_done,
    #                                                                                each.purchase_line_id.product_uom,
    #                                                                                rounding_method="HALF-UP")
    #                         if qty > quantity_done:
    #                             qty = quantity_done
    #                         if quantity_done > each.purchase_line_id.product_qty:
    #                             qty = quantity_done
    #                         if qty > 0:
    #                             invoice_id.write({'purchase_id': each.purchase_line_id.order_id.id})
    #                             prepare_invoice_line_vals = each.purchase_line_id._prepare_account_move_line(invoice_id)
    #                             prepare_invoice_line_vals.update({
    #                                 'quantity': qty
    #                             })
    #                             inv_line_vals.append((0, 0, prepare_invoice_line_vals))
    #                 if inv_line_vals:
    #                     invoice_id.write({'invoice_line_ids': inv_line_vals})
    #                 else:
    #                     raise ValidationError(_("There's nothing left to bill '%s'" % picking.name))
    #                 picking.write({'invoice_ids': [(4, invoice_id.id)], })
    #     # self.invoice_line_ids = False
    #     for eachinv in new_invoices:
    #         for line in eachinv.line_ids:
    #             if eachinv.move_type == 'in_invoice':
    #                 line.update({
    #                     'x_location_id': self.location_dest_id.id,
    #                     'x_type_transfer': 'in',
    #                 })
    #             elif eachinv.move_type == 'in_refund':
    #                 line.update({
    #                     'x_location_id': self.location_id.id,
    #                     'x_type_transfer': 'out',
    #                 })
    #         eachinv._compute_amount()
    #         eachinv.action_post()
    #         if not eachinv.invoice_line_ids:
    #             eachinv.sudo().unlink()
    #
    #     if self.purchase_id:
    #         if all([picking.state == 'done' for picking in self.purchase_id.picking_ids]):
    #             self.purchase_id.state = 'done'
    #     if self.sale_id:
    #         if all([picking.state == 'done' for picking in self.sale_id.picking_ids]):
    #             self.sale_id.state = 'done'
    #     return res

    def default_invoice_line(self, invoice_date, group_by_partner):
        picking_ids = self
        invoice_date = invoice_date or datetime.now().today().date()
        if any([not picking.partner_id for picking in picking_ids]):
            raise ValidationError(_("Partner not found. For create invoice, into picking must have the partner."))
        picking_code_lst = picking_ids.mapped('picking_type_code')
        if 'internal' in picking_code_lst:
            raise ValidationError(_("Select only Delivery Orders / Receipts for create Invoice."))
        if len(set(picking_code_lst)) > 1:
            raise ValidationError(_("Selected picking must have same Operation Type."))
        # if not self.journal_id:
        #     raise UserError(_('Please define an accounting sales journal for this company.'))

        if any([picking.state not in ['done'] for picking in picking_ids]):
            raise ValidationError(_("Selected picking must have in Done State."))
        groupby_lst = {}
        for picking_id in picking_ids.filtered(lambda l: l.state == 'done'):
            # if picking_id.invoice_ids.filtered(lambda x: x.state != 'cancel') or not picking_id.move_lines:
            #     continue
            if group_by_partner:
                key = picking_id.partner_id.id
            else:
                key = picking_id.id
            groupby_lst.setdefault(key, [])
            groupby_lst[key].append(picking_id)
        self_invoice_line_ids = []
        for lst_items in groupby_lst.values():
            for picking in lst_items:
                inv_line_vals = []
                for each in picking.move_lines:
                    if each.sale_line_id and each.sale_line_id.qty_to_invoice > 0:
                        qty = each.sale_line_id.qty_to_invoice
                        quantity_done = each.product_uom._compute_quantity(each.quantity_done,
                                                                           each.sale_line_id.product_uom,
                                                                           rounding_method="HALF-UP")
                        if qty > quantity_done:
                            qty = quantity_done
                        prepare_invoice_line_vals = each.sale_line_id._prepare_invoice_line()
                        prepare_invoice_line_vals.update({
                            'quantity': qty,
                            'price_subtotal': qty * prepare_invoice_line_vals['price_unit']
                        })
                        inv_line_vals.append((0, 0, prepare_invoice_line_vals))
                        self_invoice_line_ids.append((0, 0, prepare_invoice_line_vals))
                    if each.purchase_line_id:
                        qty = each.purchase_line_id.product_qty - each.purchase_line_id.qty_invoiced
                        quantity_done = each.product_uom._compute_quantity(each.quantity_done,
                                                                           each.purchase_line_id.product_uom,
                                                                           rounding_method="HALF-UP")
                        if qty > quantity_done:
                            qty = quantity_done
                        if quantity_done > each.purchase_line_id.product_qty:
                            qty = quantity_done
                        if qty > 0:
                            prepare_invoice_line_vals = self._po_prepare_account_move_line(each.purchase_line_id,
                                                                                           invoice_date)
                            prepare_invoice_line_vals.update({
                                'quantity': qty,
                                'price_subtotal': qty * each.purchase_line_id.price_unit
                            })
                            inv_line_vals.append((0, 0, prepare_invoice_line_vals))
                            self_invoice_line_ids.append((0, 0, prepare_invoice_line_vals))
        return self_invoice_line_ids

    def _po_prepare_account_move_line(self, purchase_line_id, invoice_date):
        if purchase_line_id.product_id.purchase_method == 'purchase':
            qty = purchase_line_id.product_qty - purchase_line_id.qty_invoiced
        else:
            qty = purchase_line_id.qty_received - purchase_line_id.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=purchase_line_id.product_uom.rounding) <= 0:
            qty = 0.0

        if purchase_line_id.currency_id == purchase_line_id.company_id.currency_id:
            currency = False
        else:
            currency = purchase_line_id.currency_id

        return {
            'name': '%s: %s' % (purchase_line_id.order_id.name, purchase_line_id.name),
            'currency_id': currency and currency.id or False,
            'purchase_line_id': purchase_line_id.id,
            'date_maturity': invoice_date,
            'date': invoice_date,
            'product_uom_id': purchase_line_id.product_uom.id,
            'product_id': purchase_line_id.product_id.id,
            'price_unit': purchase_line_id.price_unit,
            'quantity': qty,
            'partner_id': purchase_line_id.partner_id.id,
            'analytic_account_id': purchase_line_id.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, purchase_line_id.analytic_tag_ids.ids)],
            'tax_ids': [(6, 0, purchase_line_id.taxes_id.ids)],
            'display_type': purchase_line_id.display_type,
        }

    def _compute_invoice_date(self):
        invoice_date = fields.Date.today()
        # purchase_id = self.env['purchase.order'].search([('name', '=', self.origin)], limit=1)
        # if purchase_id:
        #     inter_sale_id = self.env['sale.order'].sudo().search(
        #         [('auto_purchase_order_id', '=', purchase_id.id), ('state', '!=', 'cancel')], limit=1)
        #     if inter_sale_id:
        #         invoice_date = inter_sale_id.invoice_ids[0].invoice_date
        return invoice_date


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_account_move_line_from_move(self, move):
        self.ensure_one()
        qty = self.quantity_done
        currency = move.currency_id
        return {
            'name': '%s: %s' % (self.origin, self.name),
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'purchase_line_id': self.purchase_line_id.id,
            'date_maturity': move.invoice_date_due,
            'product_uom_id': self.product_uom.id,
            'product_id': self.product_id.id,
            'price_unit': self.purchase_line_id.price_unit,
            'quantity': qty,
            'partner_id': move.partner_id.id,
            'analytic_account_id': self.purchase_line_id.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.purchase_line_id.analytic_tag_ids.ids)],
            'tax_ids': [(6, 0, self.purchase_line_id.taxes_id.ids)],
            'display_type': self.purchase_line_id.display_type,
        }

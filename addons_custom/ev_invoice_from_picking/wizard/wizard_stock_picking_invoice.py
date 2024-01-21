# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo.tools.float_utils import float_compare

# TienNQ add type
journal_type_dict = {
    ('outgoing', 'customer'): ['out_invoice'],
    ('outgoing', 'supplier'): ['in_refund'],
    ('incoming', 'supplier'): ['in_invoice'],
    ('incoming', 'customer'): ['out_refund'],
}


class StockPickingInvoive(models.TransientModel):
    _name = 'wizard.stock.picking.invoice'
    _description = "Wizard Stock Picking Description"

    journal_id = fields.Many2one('account.journal', string="Journal", required=True)
    invoice_type = fields.Selection([('out_invoice', 'Create Customer Invoice'),
                                     ('out_refund', 'Create Customer Credit Note'),
                                     ('in_invoice', 'Create Vendor Bill'),
                                     ('in_refund', 'Create Vendor Refund')], 'Invoice Type', readonly=True)
    invoice_date = fields.Date(string="Invoice Date")
    group_by_partner = fields.Boolean(string="Group By Partner", default=True)
    invoice_line_ids = fields.Many2many('account.move.line', string="Invoice Detail")

    @api.model
    def default_get(self, fieldslist):
        res = super(StockPickingInvoive, self).default_get(fieldslist)
        context = self.env.context
        picking_ids = context and context.get('active_ids', [])
        pickings = self.env['stock.picking'].browse(picking_ids)
        pick = pickings and pickings[0]
        if not pick or not pick.move_lines:
            return {}
        type = pick.picking_type_code
        usage = pick.move_lines[0].location_id.usage if type == 'incoming' else pick.move_lines[
            0].location_dest_id.usage
        for picking_id in pickings:
            x_type = picking_id.picking_type_code
            x_usage = picking_id.move_lines[0].location_id.usage if type == 'incoming' else picking_id.move_lines[
                0].location_dest_id.usage
            if x_type != type or x_usage != usage:
                raise ValidationError(_("Select only type Delivery / Receipts for create Invoice."))
        self_invoice_line_ids = self.default_invoice_line()
        # if len(self_invoice_line_ids) > 0:
        #     self.invoice_line_ids = self_invoice_line_ids

        res.update({'invoice_type': journal_type_dict.get((type, usage), [''])[0],
                    'invoice_line_ids': self_invoice_line_ids})
        return res

    @api.onchange('invoice_type')
    def _onchange_invoice_type(self):
        domain = [('type', 'in', {'out_invoice': ['sale'],
                                  'out_refund': ['sale'],
                                  'in_refund': ['purchase'],
                                  'in_invoice': ['purchase']}.get(self.invoice_type, [])),
                  ('company_id', '=', self.env.user.company_id.id)]
        domain = domain
        return {'domain': {'journal_id': domain}}

    def create_invoice(self):
        # self.invoice_line_ids = False
        picking_ids = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        invoice_date = self.invoice_date or datetime.now().today().date()
        if any([not picking.partner_id for picking in picking_ids]):
            raise ValidationError(_("Partner not found. For create invoice, into picking must have the partner."))
        picking_code_lst = picking_ids.mapped('picking_type_code')
        if 'internal' in picking_code_lst:
            raise ValidationError(_("Select only Delivery Orders / Receipts for create Invoice."))
        if len(set(picking_code_lst)) > 1:
            raise ValidationError(_("Selected picking must have same Operation Type."))
        if not self.journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        if any([picking.state not in ['done'] for picking in picking_ids]):
            raise ValidationError(_("Selected picking must have in Done State."))
        groupby_lst = {}
        for picking_id in picking_ids.filtered(lambda l: l.state == 'done'):
            # if picking_id.invoice_ids.filtered(lambda x: x.state != 'cancel') or not picking_id.move_lines:
            #     continue
            if self.group_by_partner:
                key = picking_id.partner_id.id
            else:
                key = picking_id.id
            groupby_lst.setdefault(key, [])
            groupby_lst[key].append(picking_id)
        new_invoices = self.env['account.move']
        for lst_items in groupby_lst.values():
            invoice_lst = {}
            for picking in lst_items:
                user_id = False
                currency_id = self.env.user.company_id.currency_id.id
                if picking.sale_id:
                    user_id = picking.sale_id.user_id.id or False
                    currency_id = picking.sale_id.pricelist_id.currency_id.id or picking.sale_id.company_id.currency_id.id
                if picking.purchase_id:
                    user_id = picking.purchase_id.user_id.id or False
                    currency_id = picking.purchase_id.currency_id.id or picking.purchase_id.company_id.currency_id.id
                key = (picking.partner_id.id, picking.company_id.id)
                invoice_vals = picking.with_context(journal_id=self.journal_id.id, invoice_date=self.invoice_date,
                                                    invoice_type=self.invoice_type, user_id=user_id,
                                                    currency_id=currency_id,
                                                    date=self.invoice_date or datetime.now().today().date())._prepare_invoice()
                if key not in invoice_lst:
                    invoice_vals.update({'date': self.invoice_date or datetime.now().today().date()})
                    invoice_id = self.env['account.move'].with_context(default_type=self.invoice_type,
                                                                       default_currency_id=currency_id).create(
                        invoice_vals)
                    invoice_lst[key] = invoice_id
                    new_invoices += invoice_id
                else:
                    invoice_id = invoice_lst[key]
                    update_inv_data = {'stock_picking_ids': [(4, picking.id)]}
                    if not invoice_id.invoice_origin or invoice_vals[
                        'invoice_origin'] not in invoice_id.invoice_origin.split(
                            ', '):
                        invoice_origin = filter(None, [invoice_id.invoice_origin, invoice_vals['invoice_origin']])
                        update_inv_data['invoice_origin'] = ', '.join(invoice_origin)
                    if invoice_vals.get('name', False) and (
                            not invoice_id.name or invoice_vals['name'] not in invoice_id.name.split(', ')):
                        invoice_name = filter(None, [invoice_id.name, invoice_vals['name']])
                        update_inv_data['name'] = ', '.join(invoice_name)
                    if update_inv_data:
                        invoice_id.write(update_inv_data)
                if invoice_id:
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
                            prepare_invoice_line_vals.update({'quantity': qty})
                            inv_line_vals.append((0, 0, prepare_invoice_line_vals))
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
                                invoice_id.write({'purchase_id': each.purchase_line_id.order_id.id})
                                prepare_invoice_line_vals = each.purchase_line_id._prepare_account_move_line(invoice_id)
                                prepare_invoice_line_vals.update({'quantity': qty})
                                inv_line_vals.append((0, 0, prepare_invoice_line_vals))
                    if inv_line_vals:
                        invoice_id.write({'invoice_line_ids': inv_line_vals})
                    else:
                        raise ValidationError(_("There's nothing left to bill '%s'" % picking.name))
                    picking.write({'invoice_ids': [(4, invoice_id.id)],
                                   })
        # self.invoice_line_ids = False
        for eachinv in new_invoices:
            eachinv._compute_amount()
            if not eachinv.invoice_line_ids:
                eachinv.sudo().unlink()
        if new_invoices:
            invoice_type = new_invoices[0].move_type
            if invoice_type == 'in_invoice':
                action = self.sudo().env.ref('account.action_move_in_invoice_type').read()[0]
            else:  # invoice_type == 'out_invoice':
                action = self.sudo().env.ref('account.action_move_out_invoice_type').read()[0]
            if len(new_invoices.ids) > 1:
                action['domain'] = [('id', 'in', new_invoices.ids)]
            else:
                action['views'] = [(self.sudo().env.ref('account.view_move_form').id, "form")]
                action['res_id'] = new_invoices.ids[0]
            return action

    def default_invoice_line(self):
        picking_ids = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        invoice_date = self.invoice_date or datetime.now().today().date()
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
            if self.group_by_partner:
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
                        prepare_invoice_line_vals.update(
                            {'quantity': qty, 'price_subtotal': qty * prepare_invoice_line_vals['price_unit']})
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
                                                                                           self.invoice_date)
                            prepare_invoice_line_vals.update(
                                {'quantity': qty, 'price_subtotal': qty * each.purchase_line_id.price_unit})
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

    @api.model
    def create(self, vals):
        # if 'invoice_line_ids' in vals:
        vals.update({'invoice_line_ids': []})
        obj = super(StockPickingInvoive, self).create(vals)
        return obj

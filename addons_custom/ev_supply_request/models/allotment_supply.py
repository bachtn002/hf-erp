# -*- coding: utf-8 -*-

import xlrd
import base64

from datetime import date
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, except_orm, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.osv import osv


class AllotmentSupply(models.Model):
    _name = 'allotment.supply'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Allotment Purchase Request'

    name = fields.Char('Name', default=lambda self: _('New'))
    date = fields.Date('Date Allotment', default=lambda x: datetime.today(), track_visibility='onchange')
    note = fields.Text('Note', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    supply_request_id = fields.Many2one('supply.request', string='Supply Name',
                                        domain=[('state', '=', 'receive'), ('line_ids', '!=', False)])
    line_ids = fields.One2many('allotment.supply.line', 'allotment_supply_id', string='Information')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], copy=False, default='draft', track_visibility='onchange')

    def action_get_supply_request(self):
        try:
            if self.line_ids:
                for line in self.line_ids:
                    line.unlink()
            vals = []
            for line in self.supply_request_id.line_ids:
                val = {
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'uom_id': line.uom_id.id,
                    'categ_id': line.categ_id.id,
                    'warehouse_dest_id': line.warehouse_dest_id.id,
                    'partner_id': line.partner_id.id,
                    'qty_request': line.qty_request,
                    'price_unit': line.price_unit,
                    'note': line.note,
                    'allotment_supply_id': self.id,
                }
                vals.append((0, 0, val))
            self.line_ids = vals
        except Exception as e:
            raise ValidationError(e)

    def action_import_line(self):
        return

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_("You cannot delete record if the state is not 'Draft'."))
        return super(AllotmentSupply, self).unlink()

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'cancel':
            return True
        self.state = 'cancel'

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'done':
            return True
        purchase_order_obj = self.env['purchase.order']
        purchase_order_line_obj = self.env['purchase.order.line']
        for line in self.line_ids:
            if line.qty_buy > 0:
                line.request_line_id.qty_apply = line.qty_buy
                if not line.partner_id:
                    raise UserError(_("You need to configure the partner'."))
                picking_type_id = self.env['stock.picking.type'].search(
                    [('warehouse_id', '=', line.warehouse_dest_id.id), ('code', '=', 'incoming')], limit=1)
                purchase_order = purchase_order_obj.search(
                    [('partner_id', '=', line.partner_id.id), ('picking_type_id', '=', picking_type_id.id),
                     ('origin', '=', self.name)], limit=1)
                if purchase_order:
                    purchase_order_line_value = self._prepare_purchase_order_line(line.product_id, line.qty_buy,
                                                                                  line.uom_id, self.company_id,
                                                                                  purchase_order.partner_id,
                                                                                  purchase_order, line.price_unit)
                    purchase_order_line_obj.create(purchase_order_line_value)
                    line.purchase_order_id = purchase_order.id
                else:
                    purchase_order_id = purchase_order_obj.create({
                        'partner_id': line.partner_id.id,
                        'date_order': self.date,
                        'picking_type_id': picking_type_id.id,
                        'origin': self.name
                    })
                    if purchase_order_id:
                        purchase_order_line_value = self._prepare_purchase_order_line(line.product_id, line.qty_buy,
                                                                                      line.uom_id, self.company_id,
                                                                                      purchase_order_id.partner_id,
                                                                                      purchase_order_id,
                                                                                      line.price_unit)
                        purchase_order_line_obj.create(purchase_order_line_value)
                        line.purchase_order_id = purchase_order_id.id
        self.supply_request_id.state = 'done'
        self.date = datetime.today()
        self.state = 'done'

    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po, price_unit):
        partner = supplier.name
        uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        # _select_seller is used if the supplier have different price depending
        # the quantities ordered.
        seller = supplier

        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes, product_id, seller.name)
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == company_id.id)

        product_lang = product_id.with_prefetch().with_context(
            lang=seller.lang,
            partner_id=seller.id,
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        # date_planned = po.date_planned or self.env['purchase.order.line']._get_date_planned(seller, po=po)
        date_planned = po.date_planned or fields.Date.today()
        return {
            'name': name,
            'product_qty': uom_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'order_id': po.id,
        }

    def action_confirm_order(self):
        self.ensure_one()
        for line in self.line_ids:
            line.purchase_order_id.button_confirm()

    def action_print_excel(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/report/xlsx/ev_supply_request.allotment_supply_xlsx/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('allotment.supply') or '/'
        d_to = datetime.today()
        name = 'AS.' + str(d_to.year) + str(d_to.strftime('%m')) + str(d_to.day)
        vals['name'] = name + '.' + seq
        return super(AllotmentSupply, self).create(vals)

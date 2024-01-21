# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_status_deposit = fields.Selection([('deposit', 'Deposit'), ('allocating', 'Allocating'),('allocated', 'Allocated')], string='Payment Type')
    x_deposit_amount = fields.Float('Deposit Amount')
    x_allocated_amount = fields.Float('Allocated amount')
    x_remaining_amount = fields.Float('Remaining Amount')
    x_payment_line_ids = fields.One2many('account.payment.line', 'purchase_order_id', 'Payment Lines')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
            return super(PurchaseOrder, self).name_search(name, args, operator, limit)
        args = args or []
        domain = ['|', ('origin', operator, name), ('name', operator, name)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()

    def action_allocate(self):
        view_id = self.env.ref('ev_account_payment.view_allocate_deposit_supplier')
        return {
            'name': _('Allocate Deposit Supplier'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'allocate.deposit.supplier',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'action': 'action_allocate_deposit_supplier',
            'context': {
                'default_purchase_order_id': self.id,
                'default_view_type': 'purchase',
                'default_partner_id': self.partner_id.id
            },
        }
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_legal_representation = fields.Char('Legal Representation')
    x_purchase_order_ids = fields.One2many('purchase.order', 'partner_id', 'Purchase Order', domain=[('x_status_deposit','in',('deposit','allocating','allocated'))])

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
                'default_partner_id': self.id,
                'default_view_type': 'partner'
            },
        }


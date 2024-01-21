# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class CheckVoucherCodeTransient(models.TransientModel):
    _name = 'check.voucher.code.transient'

    name = fields.Char(_('Voucher Code'))
    x_order_id = fields.Many2one('pos.order', 'Order', readonly=True)
    x_order_use_id = fields.Many2one('pos.order', 'Order use', readonly=True)
    x_customer_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    x_use_customer_id = fields.Many2one('res.partner', 'Use customer', readonly=True)
    x_total_count = fields.Float('Total count', readonly=True)
    x_use_count = fields.Float('Use count', readonly=True)
    x_state = fields.Selection(selection=[
        ('new', 'New'),
        ('activated', 'Activated'),
        ('available', 'Available'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('destroy', 'Destroy'),
        ('lock', 'Lock')
    ], default='new', string='State', )
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)

    check = fields.Boolean('Check Invisible Update voucher', default=False)

    def check_voucher_code(self):
        try:
            voucher_record = self.env['stock.production.lot'].search([('name', '=', self.name)])
            if voucher_record:
                self.x_order_use_id = voucher_record.x_order_use_id
                self.x_state = voucher_record.x_state
                self.check = True
        except Exception as e:
            raise ValidationError(e)

    # def update_voucher_code(self):
    #     try:
    #         voucher_record = self.env['stock.production.lot'].search([('name', '=', self.name)])
    #         if voucher_record:
    #             if not self.x_order_use_id:
    #                 date = datetime.strftime(datetime.today().now() + relativedelta(hours=7), '%d/%m/%Y %H:%M:%S')
    #                 state_before = voucher_record.x_state
    #                 state = self.x_state
    #                 voucher_record.update({
    #                     'x_state': state,
    #                 })
    #                 if state_before != self.x_state:
    #                     self.env['change.voucher.code'].sudo().create(
    #                         {'name': self.name,
    #                          'state_before': state_before,
    #                          'state_after': self.x_state,
    #                          'user_change': self.current_user.name,
    #                          'datetime': str(date)
    #                          })
    #                     self.env.cr.commit()
    #                 self.check = False
    #             else:
    #                 raise UserError(_('Voucher not update'))
    #     except Exception as e:
    #         raise ValidationError(e)

# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import fields, models, api, _


class CheckPromotionCode(models.TransientModel):
    _name = 'check.promotion.code'

    name = fields.Char('Promotion Code')

    total_count = fields.Float('Total count user', readonly=True)
    promotion_use_code = fields.Integer('Promotion Use Code')
    promotion_use_code_old = fields.Integer('Promotion Use Code')
    promotion_id = fields.Many2one('pos.promotion', 'Promotion Vourcher')
    promotion_line_id = fields.Many2one('promotion.voucher.line', 'Promotion Vourcher Line')
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('available', 'Available'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('destroy', 'Destroy')
    ], default=None, string='State')
    state_before = fields.Selection(selection=[
        ('new', 'New'),
        ('available', 'Available'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('destroy', 'Destroy')
    ], default=None, string='State')
    user_id = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    check = fields.Boolean('Check Invisible Update Promotion Code', default=False)
    line_ids = fields.One2many('check.promotion.code.line', 'check_promotion_code_id', 'List Order')

    def check_promotion_code(self):
        try:
            self.line_ids.unlink()
            promotion_code = self.env['promotion.voucher.line'].search([('name', '=', self.name)])
            promotion_code_count = self.env['promotion.voucher.count'].search([('promotion_code', '=', self.name)])
            order_ids = self.env['pos.order.line'].search([('promotion_code', '=', self.name)])
            if promotion_code:
                if promotion_code_count:
                    self.total_count = len(promotion_code_count)
                self.state = promotion_code.state_promotion_code
                self.promotion_id = promotion_code.promotion_id.id
                self.promotion_use_code = promotion_code.promotion_use_code
                self.promotion_line_id = promotion_code.id
                vals = []
                for order in order_ids:
                    val = {
                        'check_promotion_code_id': self.id,
                        'order_id': order.order_id.id,
                        'phone': order.order_id.partner_id.phone if order.order_id.partner_id else False,
                    }
                    vals.append((0, 0, val))
                self.line_ids = vals
            else:
                raise UserError(_('Promotion Code do not exit'))
        except Exception as e:
            raise ValidationError(e)

    # def update_promotion_code(self):
    #     try:
    #         if self.total_count < self.promotion_use_code:
    #             date = datetime.strftime(datetime.today().now() + relativedelta(hours=7), '%d/%m/%Y %H:%M:%S')
    #             if self.state_before != self.state or self.promotion_use_code_old != self.promotion_use_code:
    #                 self.env['change.promotion.code'].sudo().create({
    #                     'name': self.name,
    #                     'state_before': self.state_before,
    #                     'state_after': self.state,
    #                     'promotion_use_code_old': self.promotion_use_code_old,
    #                     'promotion_use_code': self.promotion_use_code,
    #                     'user_change': self.user_id.name,
    #                     'datetime': str(date)
    #                 })
    #                 self.env.cr.commit()
    #             if self.promotion_line_id.state_promotion_code != self.state:
    #                 self.promotion_line_id.state_promotion_code = self.state
    #             if self.promotion_line_id.promotion_voucher_id.promotion_use_code != self.promotion_use_code:
    #                 self.promotion_line_id.promotion_use_code = self.promotion_use_code
    #             self.check = False
    #         else:
    #             raise UserError(_('Promotion Not Update'))
    #     except Exception as e:
    #         raise ValidationError(e)

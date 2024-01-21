# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UpdatePromotionCode(models.TransientModel):
    _name = 'update.promotion.code'

    expired_type = fields.Selection(string=_('Expired type selection'),
                                    selection=[('fixed', 'Fixed'), ('flexible', 'Flexible')],
                                    help=_(
                                        'Flexible : applies to the number of months entered from the activation date - Fixed : applies to the date entered from the activation date'))
    date = fields.Date('Date start')
    expired_date = fields.Date(_('Expired date'))
    promotion_id = fields.Many2one('pos.promotion', 'Pos Promotion')
    promotion_use_code = fields.Integer('Promotion Use Code', default=None)

    def action_update(self):
        try:
            promotion_code = self.env['promotion.voucher'].browse(self._context.get('active_id'))
            for record in promotion_code:
                if self.expired_type:
                    record.expired_type = self.expired_type
                    record.expired_date = None
                    for line in record.promotion_voucher_line:
                        if line.state_promotion_code not in ('used', 'destroy'):
                            line.expired_date = None
                if self.expired_date and self.expired_type != 'flexible':
                    record.expired_date = self.expired_date
                if self.promotion_id:
                    record.promotion_id = self.promotion_id
                if self.promotion_use_code:
                    record.promotion_use_code = self.promotion_use_code
                    for line in record.promotion_voucher_line:
                        if line.state_promotion_code not in ('used', 'destroy'):
                            line.promotion_use_code = self.promotion_use_code
                if self.date:
                    record.date = self.date
        except Exception as e:
            raise ValidationError(e)

# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class WriteReasonRefuse(models.TransientModel):
    _name = 'write.reason.refuse'

    reason = fields.Text(string='Reason')

    def write_reason(self):
        try:
            pos_order = self.env['pos.order'].browse(self._context.get('active_id'))
            if pos_order:
                if not pos_order.x_pos_send_return:
                    raise UserError(_('Order not send return'))
                pos_order.x_reason_refuse = self.reason
                pos_order.x_pos_send_return = False
        except Exception as e:
            raise ValidationError(e)

# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import ValidationError


class SaleRequestNotification(models.TransientModel):
    _name = 'sale.request.notification'

    def confirm_notification(self):
        try:
            sale_request = self.env['sale.request'].browse(self._context.get('active_id'))
            if sale_request:
                sale_request.action_get_line_forecast()
        except Exception as e:
            raise ValidationError(e)

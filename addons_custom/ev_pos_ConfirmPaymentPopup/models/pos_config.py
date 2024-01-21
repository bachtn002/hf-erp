# -*- coding: utf-8 -*-
from odoo import _, models, api, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    x_show_popup_payment_confirm = fields.Boolean(_('Show Confirm Payment Popup'), copy=True)

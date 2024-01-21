# -*- coding: utf-8 -*-

import odoo
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.safe_eval import safe_eval
import ast


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def _get_domain_access_right(self, result):
        result = super(IrActionsActWindow, self)._get_domain_access_right(result)
        for values in result:
            model = values.get('res_model')
            if model == 'product.process':
                values['domain'] = self._get_warehouse_access_right(field='warehouse_id', domain=values.get('domain'))
        return result
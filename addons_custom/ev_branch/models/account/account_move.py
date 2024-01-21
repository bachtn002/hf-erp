# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _default_branch_id(self):
        if not self._context.get('branch_id'):
            branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        else:
            branch_id = self._context.get('branch_id')
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id, required=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _default_branch_id(self):
        if not self._context.get('branch_id'):
            branch_id = self.env['res.users'].browse(self._uid).branch_id.id
        else:
            branch_id = self._context.get('branch_id')
        return branch_id

    branch_id = fields.Many2one('res.branch', default=_default_branch_id, required=True)

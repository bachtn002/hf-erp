# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    branch_ids = fields.Many2many('res.branch','res_users_branch_rel','user_id','branch_id',string="Allowed Branch", required=True)
    branch_id = fields.Many2one('res.branch', string= 'Branch', required=True)


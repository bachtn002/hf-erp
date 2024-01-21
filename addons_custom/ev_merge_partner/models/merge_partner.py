from odoo import fields, models, api, _
from datetime import date

from odoo.exceptions import UserError, ValidationError


class MergePartner(models.Model):
    _name = 'merge.partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Name', default='New')
    date = fields.Date(string='Date', default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', string='Partner', domain=[('active', '=', True)])
    partner_merge_id = fields.Many2one('res.partner', string='Partner Merge', domain=[('active', '=', False)])

    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')], string="State",
        default='draft', track_visibility='always')

    def action_merge(self):
        try:
            if self.partner_id.id == self.partner_merge_id.id or self.partner_id.phone != self.partner_merge_id.phone:
                raise UserError(_('You can not merge one partner'))
            self.partner_id.loyalty_points += self.partner_merge_id.loyalty_points
            self.partner_merge_id.loyalty_points = 0

            query = """
                update pos_order
                set partner_id = %s
                where partner_id = %s
            """ % (self.partner_id.id, self.partner_merge_id.id)

            self._cr.execute(query)
            self.state = 'done'

        except Exception as e:
            raise ValidationError(e)

    @api.model
    def create(self, vals):
        try:
            date_merge = fields.date.today().strftime('%d-%m-%Y')
            vals['name'] = _('Merge partner date: ') + date_merge
            return super(MergePartner, self).create(vals)
        except Exception as e:
            raise ValidationError(e)

from odoo import models, fields, api, _
from odoo.models import NewId


class FloatingRate(models.Model):
    _name = 'loan.floating.rate'
    _inherit = 'mail.thread'
    _order = 'date_from desc, id'
    _description = 'Floating Rate Line'

    rate = fields.Float(string='Rate (%)', tracking=True)
    date_from = fields.Date(string='Valid From', required=True, default=fields.Date.today(), store=True, index=True, tracking=True)
    date_to = fields.Date(string='Valid To', compute='_compute_date_to', store=True, index=True,
                          tracking=True,
                          help="The date before which the rate is valid")
    interest_date_type_id = fields.Many2one('loan.interest.rate.type', string='Rate Type', required=True, ondelete='cascade')

    _sql_constraints = [
        ('date_from_unique',
         'UNIQUE(interest_date_type_id, date_from)',
         "The date specified the Valid From must be unique per Rate Type."),
    ]

    @api.depends('date_from', 'interest_date_type_id.floating_rate_ids.date_from')
    def _compute_date_to(self):
        for r in self:
            if isinstance(r.id, NewId):
                continue
            next_line_id = self.search([
                ('id', '!=', r.id),
                ('interest_date_type_id', '=', r.interest_date_type_id.id),
                ('date_from', '>', r.date_from)], order='date_from asc, id', limit=1)
            if next_line_id:
                r.date_to = next_line_id.date_from
            else:
                r.date_to = False

    def _get_display_name(self):
        interest_rate_period = dict(self.interest_date_type_id._fields['interest_rate_period']._description_selection(self.env)).get(self.interest_date_type_id.interest_rate_period)
        if self.date_to == 'flat':
            name = '%s%s%s%s' % (_("From "), self.date_from, _(" To "), self.date_to)
        else:
            name = '%s%s' % (_("From "), self.date_from)

        name = '%s %s [%s]' % (str(self.rate) + '%', interest_rate_period, name)
        return name

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, rec._get_display_name()))
        return res


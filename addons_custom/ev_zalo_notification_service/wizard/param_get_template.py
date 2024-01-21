from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError
from ..helpers import APIZNS


class ParamGetTemplate(models.TransientModel):
    _name = 'param.get.template'
    _description = 'Create a Param get list template'

    offset = fields.Integer('Offset', help='The order of the first template in the returned list.' +
                                           'Note: The most recently created Template will have an order of 0.')
    limit = fields.Integer('Limit', help='Maximum 100')
    status = fields.Selection([
        ('1', 'Enable'),
        ('2', 'Pending'),
        ('3', 'Reject'),
        ('4', 'Disable'),
        ('5', 'Delete'),
    ], 'Status', default=None)

    def get_template(self):
        try:
            if self.limit > 100:
                raise UserError(_('Limit must be less than 100'))
            status = int(self.status) if self.status else False
            zns_id = self.env['zalo.token'].browse(self._context.get('active_id'))
            template_ids = APIZNS.get_template(zns_id, self.offset, self.limit, status)

            for template in template_ids:
                APIZNS.get_template_detail(template)
        except Exception as e:
            raise ValidationError(e)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class MapZNSConfig(models.Model):
    _name = 'map.zns.config'
    _description = 'Map ZNS config'
    _order = 'create_date desc'

    model = fields.Char('Model', required=True, index=True)
    param_erp = fields.Char('Param ERP', required=True, index=True)
    param_zns = fields.Char('Param ZNS', required=True, index=True)
    template_id = fields.Char('Template ID', required=True, index=True)
    active = fields.Boolean('Active', default=True)

    @api.model
    def create(self, vals):
        try:
            map_zns_config = self.search([('model', '=', vals.get('model')),
                                          ('param_erp', '=', vals.get('param_erp')),
                                          ('param_zns', '=', vals.get('param_zns')),
                                          ('template_id', '=', vals.get('template_id'))])
            if map_zns_config:
                raise UserError(_('This information already exists, please edit'))
            return super(MapZNSConfig, self).create(vals)
        except Exception as e:
            raise ValidationError(e)

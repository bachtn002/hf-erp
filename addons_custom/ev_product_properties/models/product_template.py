from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    _sql_constraints = [
        ('default_code_uniq', 'unique (default_code)',
         'The default code must be unique!')
    ]

    @api.model
    def create(self, vals):
        try:
            if not vals['default_code']:
                return super(ProductTemplate, self).create(vals)
        except:
            return super(ProductTemplate, self).create(vals)
        try:
            if vals['default_code']:
                sql = "Select * from product_template where default_code = '%s'"
                self._cr.execute(sql % (vals['default_code']))
                result = self._cr.dictfetchall()
                if result:
                    raise UserError(_('The default code must be unique!'))
                else:
                    res = super(ProductTemplate, self).create(vals)
                    if len(res.taxes_id.ids) > 1:
                        raise UserError(_('Taxes cannot have more 1 values'))
                    return res

        except Exception as e:
            raise ValidationError(e)

    def write(self, vals):
        if 'active' in vals:
            not_archive_product = []
            for record in self:
                if not vals['active']:
                    if record.qty_available > 0:
                        not_archive_product.append(record.name)
            if not_archive_product:
                message = ""
                for name in not_archive_product:
                    message += name + '\n'
                raise UserError(_('Cannot archive product if quantity available > 0. Product:\n %s', message))

        if 'taxes_id' in vals:
            if len(vals['taxes_id'][0][2]) > 1:
                raise UserError(_('Taxes cannot have more 1 values'))
        try:
            if not vals['default_code']:
                return super(ProductTemplate, self).write(vals)
        except:
            return super(ProductTemplate, self).write(vals)
        try:
            if vals['default_code'] and vals['default_code'] != self.default_code:
                sql = "Select * from product_template where default_code = '%s'"
                self._cr.execute(sql % (vals['default_code']))
                result = self._cr.dictfetchall()
                if result:
                    raise UserError(_('The default code must be unique!'))
                else:
                    return super(ProductTemplate, self).write(vals)

        except Exception as e:
            raise ValidationError(e)

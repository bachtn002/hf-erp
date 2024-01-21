from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProductOtherConfig(models.Model):
    _name = 'product.other.config'
    _rec_name = 'promotion_id'

    promotion_id = fields.Many2one('pos.promotion', 'Pos Promotion',
                                   domain=[('end_date', '>=', datetime.today()), ('state', '=', 'active'),
                                           ('type', '!=', 'qty_price')])
    other_line_ids = fields.One2many(comodel_name='product.other.config.line', inverse_name='other_config_id',
                                     string="Print Stamp Other Line")

    # _sql_constraints = [
    #     ('promotion_id_uniq', 'unique(promotion_id)', 'Promotion id must be unique !')
    # ]

    @api.constrains('promotion_id')
    def _constrains_promotion_id(self):
        try:
            config = self.env['product.other.config'].search([('promotion_id', '=', self.promotion_id.id)])
            if config and config != self:
                raise UserError(_('Promotion id must be unique !'))
        except Exception as e:
            raise ValidationError(e)

    @api.onchange('other_line_ids')
    def _onchange_promotion_id_set_line(self):
        try:
            if self.promotion_id:
                lines = self.env['pos.promotion'].search([('id', '=', self.promotion_id.id)])
                self.other_line_ids.packed_date = lines.start_date
                self.other_line_ids.expire_date = lines.end_date

        except Exception as e:
            raise ValidationError(e)

    def open_import_other_config(self):
        return {
            'name': 'Import Other Config',
            'type': 'ir.actions.act_window',
            'res_model': 'import.xls.other.config',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'current_id': self.id},
        }

    def get_import_other_config_template(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/ev_print_stamp_product/static/xls/imp_other_config.xlsx'
        }

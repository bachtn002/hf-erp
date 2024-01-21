from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductLotRule(models.Model):
    _name = 'product.lot.rule'
    _description = 'Product Lot Rule'

    name = fields.Char('Rule Name', required=True)
    rule_len = fields.Integer('Rule Length', required=True)
    active = fields.Boolean('Active', default=True)
    max_value_from_default_code = fields.Integer('Max value default code', default = 0)
    product_lot_rule_line_ids = fields.One2many('product.lot.rule.line', 'product_lot_rule_id', 'Product Lot Rule Line Ids')

    _sql_constraints = [
        ('name_unique', 'unique (name)', 'The name must be unique!')
    ]

    # Kiểm tra ràng buộc
    @api.constrains('product_lot_rule_line_ids')
    def _check_line_ids(self):
        if self.rule_len <= 0:
            raise ValidationError(_('Attention: Rule len must be different 0'))
        for record in self:
            # bỏ trống
            if len(record.product_lot_rule_line_ids) == 0:
                raise ValidationError('This rule have 0 line ')
            # check length
            elif len(record.product_lot_rule_line_ids) == 1:
                line = record.product_lot_rule_line_ids
                if line.type == 'fix' and len(line.fix_value) != self.rule_len:
                    raise ValidationError(_('Attention: Length of fix value is not equal rule length'))
            else:
                # check length
                if len(record.product_lot_rule_line_ids) == 2:
                    rule_ids = self.env['product.lot.rule.line'].search([('product_lot_rule_id', '=', self.id)], order='type')
                    if (len(rule_ids[0].fix_value) + len(str(rule_ids[1].start_increment))) > self.rule_len:
                        raise ValidationError(_('Attention: Length of fix value and start increment is greater than rule length !'))
                    if rule_ids[1].start_increment < 1:
                        raise UserError(_('Start increment must be greater than 0'))
                else:
                    raise ValidationError(_('Attention: Not more than 2 lines '))
    
    # Generate mã sản phẩm
    def action_generate_product_code(self):
        try:
            code = ''
            rule_ids = self.env['product.lot.rule.line'].search([('product_lot_rule_id', '=', self.id)], order='type')
            if len(rule_ids.ids) == 1:
                if rule_ids.type == 'fix':
                    code += rule_ids.action_generate_code_rule()
                else:
                    max_value = self.max_value_from_default_code
                    if max_value > rule_ids.last_sequence:
                        rule_ids.last_sequence = max_value
                    else:
                        rule_ids.last_sequence = code
                    code += rule_ids.action_generate_code_rule()
                return code
            else:
                fix_value = rule_ids[0].fix_value
                max_value = self.max_value_from_default_code

                if max_value > rule_ids[1].last_sequence:
                    rule_ids[1].last_sequence = max_value
                    start_increment = rule_ids[1].action_generate_code_rule_mix(fix_value)
                    # rule_ids[1].last_sequence = start_increment
                else:
                    start_increment = rule_ids[1].action_generate_code_rule_mix(fix_value)
                    rule_ids[1].last_sequence = start_increment

                code = fix_value + start_increment
                return code
        except Exception as e:
            raise ValidationError(e)
        


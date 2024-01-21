from email.policy import default
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductLotRuleLine(models.Model):
    _name = 'product.lot.rule.line'
    _description = 'Product Lot Rule Line'
    
    name = fields.Char('Name')
    type = fields.Selection([
        ('fix','Fix'),
        ('increment','Increment')
    ], string="Type")
    fix_value = fields.Char('Fix Value')
    start_increment = fields.Integer('Start Increment', default=1)
    last_sequence = fields.Integer('Last Sequence')
    product_lot_rule_id = fields.Many2one('product.lot.rule','Product Lot Rule ID')

    # Generate mã từng kiểu
    def action_generate_code_rule(self):
        try:
            if self.type == 'fix':
                value = self._generate_code_type_fix()
                return value
            if self.type == 'increment':
                value = self._generate_code_type_increment()
                return value
        except Exception as e:
            raise ValidationError(e)

    # Generate mã kết hợp
    def action_generate_code_rule_mix(self, value):
        try:
            fix_value = value
            rule_len = self.product_lot_rule_id.rule_len
            if self.type == 'increment':
                if self.last_sequence == 0:
                    value = '0' * (rule_len - len(value) - len(str(self.start_increment))) + str(int(self.start_increment))
                else:
                    value = '0' * (rule_len - len(value) - len(str(self.last_sequence + 1))) + str(self.last_sequence + 1)
                if len(value) > (rule_len - len(fix_value)):
                    raise ValidationError(_("Number product code of rule is max"))
                return value
        except Exception as e:
            raise ValidationError(e)

    # Generate mã cố định
    def _generate_code_type_fix(self):
        try:
            return self.fix_value
        except Exception as e:
            raise ValidationError(e)

    # Generate mã tự tăng
    def _generate_code_type_increment(self):
        try:
            rule_len = self.product_lot_rule_id.rule_len
            if self.last_sequence == 0:
                value = '0' * (rule_len - len(str(self.start_increment))) + str(int(self.start_increment))
            else: 
                value = '0' * (rule_len - len(str(self.last_sequence + 1))) + str(self.last_sequence + 1)
            if len(value) > rule_len:
                raise ValidationError(_("Number product code of rule is max"))
            return value
        except Exception as e:
            raise ValidationError(e)

    
        



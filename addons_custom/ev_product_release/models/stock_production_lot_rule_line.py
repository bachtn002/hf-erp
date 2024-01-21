from odoo import api, fields, models, _
import datetime
import string
import random
from odoo.exceptions import ValidationError


class StockProductionLotRuleLine(models.Model):
    _name = 'stock.production.lot.rule.line'

    rule_id = fields.Many2one('stock.production.lot.rule')
    type = fields.Selection(selection=[
        ('fix', 'Fix'),
        ('random', 'Random'),
        ('increment', 'Increment'),
        ('date', 'Date')
    ], required=False, string="Type")
    name = fields.Char('name', compute='_depends_type')
    sequence = fields.Integer('Sequence')
    value = fields.Char('Value')
    length = fields.Integer('Length')
    start = fields.Integer('Start', default=1)
    last_sequence = fields.Integer()
    step = fields.Integer('Step', default=1)

    @api.depends('type')
    def _depends_type(self):
        for i in self:
            i.name = i.type

    @api.onchange('type')
    def onchange_type_date(self):
        if self.type == 'date':
            self.value = '%(y)s%(month)s'

    def action_generate_code_rule(self):
        if self.type == 'fix':
            value = self._generate_code_type_fix()
            return value
        if self.type == 'random':
            value = self._generate_code_type_random()
            return value
        if self.type == 'increment':
            value = self._generate_code_type_increment()
            return value
        if self.type == 'date':
            value = self._generate_code_type_date()
            return value

    def _generate_code_type_fix(self):
        return self.value

    def _generate_code_type_random(self):
        value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(self.length))
        return value

    def _generate_code_type_date(self):
        year = datetime.date.today().strftime('%Y')
        month = datetime.date.today().strftime('%m')
        day = datetime.date.today().strftime('%d')
        y = datetime.date.today().strftime('%y')
        value = self.value % {"year": year, "y": y, "month": month, "day": day}
        return value

    def _generate_code_type_increment(self):
        if self.last_sequence == 0:
            value = '0' * (self.length - len(str(self.start))) + str(self.start)
        else:
            value = '0' * (self.length - len(str(self.last_sequence + self.step))) + str(self.last_sequence + self.step)
        if len(value) > self.length:
            raise ValidationError(_("Rule's length: {} greater allowable length {}").format(self.type, self.length))
        return value

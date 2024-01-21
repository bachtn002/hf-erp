from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockProductionLotRule(models.Model):
    _name = 'stock.production.lot.rule'

    name = fields.Char('Name', default=lambda self: _('New'))
    active = fields.Boolean('Active', default=True)
    production_lot_rule_ids = fields.One2many('stock.production.lot.rule.line', 'rule_id', 'Details')

    def action_generate_code(self, code_lots):
        code = ''
        rule_ids = self.env['stock.production.lot.rule.line'].search([('rule_id', '=', self.id)], order='sequence')
        for rule_id in rule_ids:
            code += rule_id.action_generate_code_rule()
        # if code in code_lots:
        #     code = self.action_generate_code(code_lots)
        for item in rule_ids:
            if item.type == 'increment':
                item.last_sequence = item._generate_code_type_increment()
        return code

    def _check_rule_length(self, length):
        if length != self.env.company.x_voucher_code_rule_length:
            raise ValidationError(_("Length of Voucher's code is different with allowable length : {}. \n"
                                    "Your rule's length: {}").format(self.env.company.x_voucher_code_rule_length,
                                                                     length))

    def _get_length_rule(self, rule_id):
        length = 0
        if rule_id.type == 'fix':
            length += len(rule_id.value)
        if rule_id.type == 'random':
            length += rule_id.length
        if rule_id.type == 'increment':
            length += rule_id.length
        if rule_id.type == 'date':
            length += len(rule_id._generate_code_type_date())
        return length

    @api.model
    def create(self, values):
        res = super(StockProductionLotRule, self).create(values)
        if res.production_lot_rule_ids:
            length = 0
            sequence = 0
            for rule_id in res.production_lot_rule_ids:
                length += self._get_length_rule(rule_id=rule_id)
                rule_id.sequence = sequence
                sequence += 1
            self._check_rule_length(length)
        return res

    def write(self, values):
        res = super(StockProductionLotRule, self).write(values)
        for item in self:
            if item.production_lot_rule_ids:
                length = 0
                for rule_id in item.production_lot_rule_ids:
                    length += self._get_length_rule(rule_id=rule_id)
                self._check_rule_length(length)
        return res

# -*- coding: utf-8 -*-

from odoo.tests import common


class TestStockProductionLotRuleLine(common.TransactionCase):

    def test_create_production_lot_rule_line_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        production_lot_rule_line = self.env['stock.production.lot.rule.line'].create({
            'name': name_space})
        self.assertEqual(production_lot_rule_line.name, name, 'Create group not remote space in name')

    def test_write_production_lot_rule_line_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        production_lot_rule_line = self.env['stock.production.lot.rule.line'].create({
            'name': name})
        production_lot_rule_line.write({'name': name_space})
        self.assertEqual(production_lot_rule.name, name, 'Write group not remote space in name')

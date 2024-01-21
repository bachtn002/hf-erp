# -*- coding: utf-8 -*-

from odoo.tests import common


class TestStockProductionLotRule(common.TransactionCase):

    def test_create_production_lot_rule_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        production_lot_rule = self.env['stock.production.lot.rule'].create({
            'name': name_space})
        self.assertEqual(production_lot_rule.name, name, 'Create group not remote space in name')

    def test_write_production_lot_rule_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        production_lot_rule = self.env['stock.production.lot.rule'].create({
            'name': name})
        production_lot_rule.write({'name': name_space})
        self.assertEqual(production_lot_rule.name, name, 'Write group not remote space in name')

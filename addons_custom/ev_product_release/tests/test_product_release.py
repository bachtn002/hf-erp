# -*- coding: utf-8 -*-

from odoo.tests import common


class TestProductRelease(common.TransactionCase):

    def test_create_production_lot_rule_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        product_release = self.env['product.release'].create({
            'name': name_space})
        self.assertEqual(product_release.name, name, 'Create group not remote space in name')

    def test_write_production_lot_rule_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        product_release = self.env['product.release'].create({
            'name': name})
        product_release.write({'name': name_space})
        self.assertEqual(product_release.name, name, 'Write group not remote space in name')

    def test_action_generate_serial(self):
        vals = {'name': 'Phiếu mua hàng',
                'state': 'draft'}
        product_release = self.env['product.release'].create(vals)
        product_release.action_generate_serial()
        self.assertEqual(product_release.state, 'created', 'Action generate serial not working')

    def test_action_cancel(self):
        vals = {'name': 'Phiếu mua hàng',
                'state': 'created'}
        product_release = self.env['product.release'].create(vals)
        product_release.action_cancel()
        self.assertEqual(product_release.state, 'cancel', 'Action cancel not working')

    def test_action_active(self):
        vals = {'name': 'Phiếu mua hàng',
                'state': 'created'}
        product_release = self.env['product.release'].create(vals)
        product_release.action_cancel()
        self.assertEqual(product_release.state, 'done', 'Action cancel not working')
# -*- coding: utf-8 -*-

from odoo.tests import common


class TestPosPromotion(common.TransactionCase):

    def test_vals_factory_strip_field_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        vals = {'name': name_space}
        vals = self.env['pos.promotion'].vals_factory(vals)
        self.assertEqual(vals['name'], name, 'Vals factory not strip field name')

    def test_create_promotion_remove_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        promotion = self.env['pos.promotion'].create({
            'name': name_space})
        self.assertEqual(promotion.name, name, 'Create group not remote space in name')

    def test_write_promotion_remove_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        promotion = self.env['pos.promotion'].create({
            'name': name})
        promotion.write({'name': name_space})
        self.assertEqual(promotion.name, name, 'Write group not remote space in name')

    def test_action_draft(self):
        vals = {'name': 'Promotion test',
                'state': 'active'}
        promotion = self.env['pos.promotion'].create(vals)
        promotion.action_draft()
        self.assertEqual(promotion.state, 'draft', 'Action active not working')

    def test_action_active(self):
        vals = {'name': 'Promotion test'}
        promotion = self.env['pos.promotion'].create(vals)
        promotion.action_active()
        self.assertEqual(promotion.state, 'active', 'Action active not working')

    def test_action_deactive(self):
        vals = {'name': 'Promotion test'}
        promotion = self.env['pos.promotion'].create(vals)
        promotion.action_deactive()
        self.assertEqual(promotion.state, 'inactive', 'Action deactive not working')

    def test_action_cancel(self):
        vals = {'name': 'Promotion test'}
        promotion = self.env['pos.promotion'].create(vals)
        promotion.action_cancel()
        self.assertEqual(promotion.state, 'cancel', 'Action cancel not working')

    def test_min_discount(self):
        vals = {
            'name': 'test_min_discount',
            'total_amount': 5000000,
            'discount': -10,
            'max_discount': 50000
        }
        promotion = self.env['pos.promotion'].create(vals)
        self.assertEqual(promotion.discount, 0, 'Min discount not working when create new record')
        promotion.write({'discount': -50})
        self.assertEqual(promotion.discount, 0, 'Min discount not worling when write exists record')

    def test_max_discount(self):
        vals = {
            'name': 'test_max_discount',
            'total_amount': 5000000,
            'discount': 110,
            'max_discount': 50000
        }
        promotion = self.env['pos.promotion'].create(vals)
        self.assertEqual(promotion.discount, 100, 'Max discount not working when create new record')
        promotion.write({'discount': 120})
        self.assertEqual(promotion.discount, 100, 'Max discount not working when write exists record')

    def test_min_of_max_discount(self):
        vals = {
            'name': 'test_min_of_max_discount',
            'total_amount': 5000000,
            'discount': 10,
            'max_discount': -50000
        }
        promotion = self.env['pos.promotion'].create(vals)
        self.assertEqual(promotion.max_discount, 0, 'Min of max discount not working when create new record')
        promotion.write({'max_discount': -1})
        self.assertEqual(promotion.max_discount, 0, 'Min of max discount not working when write exists record')

    def test_max_of_max_discount(self):
        vals = {
            'name': 'test_max_of_max_discount',
            'total_amount': 5000000,
            'discount': 10,
            'max_discount': 5100000
        }
        promotion = self.env['pos.promotion'].create(vals)
        self.assertEqual(promotion.max_discount, 5000000, 'Max of max discount not working when create new record')
        promotion.write({'max_discount': 5000001})
        self.assertEqual(promotion.max_discount, 5000000, 'Max of max discount not working when write exists record')

# -*- coding: utf-8 -*-

from odoo.tests import common


class TestPosPromotionTotalAmount(common.TransactionCase):

    def test_min_discount(self):
        vals = {
            'total_amount': 5000000,
            'discount': -10,
            'max_discount': 50000
        }
        promotion = self.env['pos.promotion.total.amount'].create(vals)
        self.assertEqual(promotion.discount, 0, 'Min discount not working when create new record')
        promotion.write({'discount': -50})
        self.assertEqual(promotion.discount, 0, 'Min discount not worling when write exists record')

    def test_max_discount(self):
        vals = {
            'total_amount': 5000000,
            'discount': 110,
            'max_discount': 50000
        }
        promotion = self.env['pos.promotion.total.amount'].create(vals)
        self.assertEqual(promotion.discount, 100, 'Max discount not working when create new record')
        promotion.write({'discount': 120})
        self.assertEqual(promotion.discount, 100, 'Max discount not working when write exists record')

    def test_min_of_max_discount(self):
        vals = {
            'total_amount': 5000000,
            'discount': 10,
            'max_discount': -50000
        }
        promotion = self.env['pos.promotion.total.amount'].create(vals)
        self.assertEqual(promotion.max_discount, 0, 'Min of max discount not working when create new record')
        promotion.write({'max_discount': -1})
        self.assertEqual(promotion.max_discount, 0, 'Min of max discount not working when write exists record')

    def test_max_of_max_discount(self):
        vals = {
            'total_amount': 5000000,
            'discount': 10,
            'max_discount': 5100000
        }
        promotion = self.env['pos.promotion.total.amount'].create(vals)
        self.assertEqual(promotion.max_discount, 5000000, 'Max of max discount not working when create new record')
        promotion.write({'max_discount': 5000001})
        self.assertEqual(promotion.max_discount, 5000000, 'Max of max discount not working when write exists record')

# -*- coding: utf-8 -*-

from odoo.tests import common


class TestResPartnerGroup(common.TransactionCase):

    def test_vals_factory_strip_field_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        vals = {'name': name_space}
        vals = self.env['res.partner.group'].vals_factory(vals)
        self.assertEqual(vals['name'], name, 'Vals factory not strip field name')

    def test_create_partner_group_remove_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        group = self.env['res.partner.group'].create({'name': name_space})
        self.assertEqual(group.name, name, 'Create group not remote space in name')

    def test_write_partner_group_remove_space_name(self):
        name = 'Xin chao'
        name_space = ' Xin chao '
        group = self.env['res.partner.group'].create({'name': name})
        group.write({'name': name_space})
        self.assertEqual(group.name, name, 'Write group not remote space in name')

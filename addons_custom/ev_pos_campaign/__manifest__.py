# -*- coding: utf-8 -*-
{
    'name': 'Promotion Campaign ',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Odoo 14 Chiến dịch CTKM',
    'description': """""",
    'category': 'Tutorials',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': [
        'base', 'point_of_sale', 'ev_pos_promotion'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/campaign_promotion.xml',
        'views/pos_promotion_inherit.xml',
        'views/menu_view.xml',

    ],
    'demo': [],
    'qweb': [],
    'images': [''],
    'installable': True,
    'auto_install': False,
    'application': True,
}

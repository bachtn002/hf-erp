# -*- coding: utf-8 -*-
{
    'name': 'Sale Online ',
    'version': '1.0',
    'sequence': 1,
    'summary': '',
    'description': """""",
    'category': 'POS',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': [
        'ev_pos_shop',
        'mail',
        'crm',
        'pos_longpolling',
        'point_of_sale'
    ],
    'data': [
        'security/sale_online_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/sale_online.xml',
        'views/sale_online_template.xml',
    ],
    'demo': [],
    'qweb': ['static/src/xml/pos_sale_online.xml'],
    'images': [''],
    'installable': True,
    'auto_install': False,
    'application': True,
}

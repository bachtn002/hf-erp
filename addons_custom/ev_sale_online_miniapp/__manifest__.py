# -*- coding: utf-8 -*-
{
    'name': "Sale Online MiniApp",

    'summary': """Sale Online MiniApp""",

    'description': """""",

    'author': "ERPViet",
    'website': "http://www.erpviet.vn.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'ev_pos_channel'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/sale_online.xml',
    ],
    'qweb': [
        'static/src/xml/pos_map.xml',
    ],
}

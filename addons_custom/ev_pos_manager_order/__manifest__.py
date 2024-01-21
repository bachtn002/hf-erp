# -*- coding: utf-8 -*-
{
    'name': 'Manager Order',
    'version': '1.0',
    'category': 'Manager Order',
    'summary': 'ERPViet',
    'description': """
""",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'depends': ['point_of_sale'],
    'data': [
        'views/assets.xml'
    ],
    'qweb': [
        'static/src/xml/manager_order_line_detail.xml',
    ],
    'installable': True,
}

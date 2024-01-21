# -*- coding: utf-8 -*-
{
    'name': "POS Display",
    'summary': """
        - Custom POS main display
        """,
    'description': """
        """,
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_display.xml',
        'views/pos_config.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/ProductScreen/*.xml',
        'static/src/xml/OrderManagementScreen/*.xml',
        'static/src/xml/Screens/FloorScreen/*.xml',
        'static/src/xml/pos.xml',
    ],

    'sequence': 90
}

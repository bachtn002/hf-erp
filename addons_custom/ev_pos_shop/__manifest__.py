# -*- coding: utf-8 -*-
{
    'name': "Pos Shop",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'pos shop',
    'version': '0.1',
    'depends': ['base', 'point_of_sale', 'stock'],
    'data': [
        'security/pos_shop_security.xml',
        'security/ir.model.access.csv',
        'views/pos_shop.xml',
        'views/pos_order.xml',
        'views/pos_session.xml',
        'views/pos_payment.xml',
        'views/pos_config.xml',
        'views/pos_users.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}

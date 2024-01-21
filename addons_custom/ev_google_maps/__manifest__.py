# -*- coding: utf-8 -*-
{
    'name': 'Google Maps',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Google Maps',
    'description': """""",
    'category': 'Google',
    'author': 'ERPViet',
    'maintainer': '',
    'website': 'https://erpviet.vn/',
    'license': 'LGPL-3',
    'depends': [
        'ev_source_order',
        'ev_sale_online',
        'ev_payment_qrcode',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'views/assets.xml',
        'views/pos_shop.xml',
        'views/sale_online.xml',
        # 'views/pos_order.xml',
    ],
    'demo': [],
    'qweb': [
        # 'static/src/xml/pos_map.xml',
    ],
    'images': [''],
    'installable': True,
    'auto_install': False,
}

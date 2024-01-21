# -*- coding: utf-8 -*-
{
    'name': 'Loyalty Program',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': '',
    'description': """
""",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_loyalty_views.xml',
        'views/pos_config_views.xml',
        'security/ir.model.access.csv',
        'views/pos_loyalty_templates.xml',
    ],
    'qweb': [
        'static/src/xml/OrderReceipt.xml',
        'static/src/xml/RewardButton.xml',
        'static/src/xml/PointsCounter.xml',
        'static/src/xml/Loyalty.xml',
    ],
    'demo': [
        'data/pos_loyalty_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
}

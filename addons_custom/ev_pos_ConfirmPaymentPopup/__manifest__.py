# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Confirm Payment Popup Custom",

    'summary': """
        Module bật tắt popup confirm payment trong cài đặt điểm bán lẻ.
    """,

    'description': """
    """,

    'author': "ErpViet",
    'website': "http://www.izisolution.vn",

    'category': 'Point Of Sale',
    'version': '0.4',

    'depends': ['base', 'web', 'mail', 'point_of_sale'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_config.xml',
        'views/assets.xml'
    ],
    'qweb': [
    ]
}

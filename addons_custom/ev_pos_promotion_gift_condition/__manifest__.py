# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion Gift Condition",

    'summary': """
        Module quản lý các chương trình khuyến mãi tặng sản phẩm dựa theo điều kiện
    """,

    'author': "ErpViet",
    'website': "http://www.izisolution.vn",

    'category': 'Point Of Sale',
    'version': '0.1',

    'depends': ['base', 'ev_pos_promotion'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_promotion.xml',
    ],
    'qweb': [

    ]
}

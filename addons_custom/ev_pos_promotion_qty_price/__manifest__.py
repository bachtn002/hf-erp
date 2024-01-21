# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion Quantity Price",

    'summary': """
        Module quản lý các chương trình khuyến mãi giá bán theo số lượng mua
    """,

    'author': "ErpViet",
    'website': "http://www.izisolution.vn",

    'category': 'Point Of Sale',
    'version': '0.1',

    'depends': ['base', 'ev_pos_promotion'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/promotion_qty_price.xml',
        'views/assets.xml',
        'views/pos_promotion.xml',
    ],
    'qweb': [

    ]
}

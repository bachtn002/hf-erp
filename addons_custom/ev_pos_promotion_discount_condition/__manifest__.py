# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion Discount Condition",

    'summary': """
      Giảm giá sản sản phẩm, nhóm sản phẩm dự theo điều kiện mua là
      sản phẩm, nhóm sản phẩm nào
    """,

    'description': """
      Giảm giá sản sản phẩm, nhóm sản phẩm dự theo điều kiện mua là
      sản phẩm, nhóm sản phẩm nào
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.com",

    'category': 'Point of sale',
    'version': '0.1',

    'depends': ['ev_pos_promotion'],

    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/pos_promotion.xml',
    ],
}

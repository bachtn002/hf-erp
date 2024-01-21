# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion Amount Total",

    'summary': """
      Khuyến mãi trên tổng đơn hàng
    """,

    'description': """
      Quản lý các chương trình khuyến mãi type=total_amount
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

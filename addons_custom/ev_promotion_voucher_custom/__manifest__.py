# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion Custom",

    'summary': """
        Module chỉnh sửa
    """,

    'description': """#ErpViet Pos Promotion

    - Giới hạn áp dụng tối đa 2 mã code khuyến mãi trên một đơn hàng
    - Cho phép CTKM được áp dụng cùng các CTKM khác
    """,

    'author': "SangNT",
    'website': "http://www.izisolution.vn",

    'category': 'Point Of Sale',
    'version': '0.4',

    'depends': ['base', 'web', 'ev_promotion_voucher', 'point_of_sale'],

    'data': [
        'views/pos_promotion_views.xml',
        'views/assets.xml',
    ],
}

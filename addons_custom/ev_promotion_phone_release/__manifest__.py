# -*- coding: utf-8 -*-
{
    'name': "Pos Promotion Phone release",

    'summary': """
        Pos Promotion Phone Release
    """,

    'description': """
        Module quản lý phát hành các chương trình khuyến mãi theo số điện thoại áp dụng trên POS.
    """,

    'author': "SangNT",
    'website': "http://www.izisolution.vn",

    'category': 'Point Of Sale',
    'version': '0.4',

    'depends': ['base', 'web', 'ev_promotion_voucher', 'point_of_sale'],

    'data': [
        'security/ir.model.access.csv',
        # views
        'views/assets.xml',
        'views/promotion_voucher_views.xml',
        'views/phone_promotion_list_views.xml',
        # report
        'report/promotion_code_phone_report.xml',
        # wizard
        'wizard/import_phone_promotion_release_views.xml',
        'wizard/promotion_voucher_confirm_views.xml',
        'wizard/update_promotion_code_views.xml',
    ],
}

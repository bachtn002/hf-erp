# -*- coding: utf-8 -*-
{
    'name': "ERPVIET POS Promotion Voucher Management",
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'category': 'pos',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ev_product_release', 'point_of_sale', 'ev_pos_promotion'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/update_promotion_code.xml',
        'views/promotion_voucher.xml',
        'views/menu_view.xml',
        'views/assets.xml',
        'data/ir_sequence_data.xml',
        'views/inherit_pos_promotion.xml',
        'views/promotion_voucher_lines.xml',
        'report/promotion_code_report.xml',
        'report/promotion_code_status_report.xml',
        'views/pos_order_line.xml',
    ],
    'qweb': [
        'static/src/xml/button/ButtonPromotionVoucher.xml',
        'static/src/xml/button/VoucherPopup.xml',
        'static/src/xml/ListPromotion.xml',
        'static/src/xml/ItemPromotion.xml'
    ],
}

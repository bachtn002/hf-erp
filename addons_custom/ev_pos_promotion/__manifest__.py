# -*- coding: utf-8 -*-
{
    'name': "ERPVIET Pos Promotion",

    'summary': """
        Module quản lý các chương trình khuyến mãi áp dụng trên POS.
    """,

    'description': """#ErpViet Pos Promotion

    Module không quản lý trực tiếp 1 chương trình khuyến mãi nào.

    Để có thể sử dụng được 1 chương trình khuyến mãi phải cài đặt thêm trong 
    **POS** -> **Thiết lập chung** -> 
    Chọn chương trình khuyến mãi muốn sử dụng.
    """,

    'author': "ErpViet",
    'website': "http://www.izisolution.vn",

    'category': 'Point Of Sale',
    'version': '0.4',

    'depends': ['base', 'web', 'mail', 'point_of_sale'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/date.xml',
        'views/assets.xml',
        'views/partner_group.xml',
        'views/res_partner.xml',
        'views/pos_promotion.xml',
        'views/pos_promotion_menuitem.xml',
        'views/partner_group_menuitem.xml',
        'views/custom_day.xml',
        'views/orderline_price_promotion.xml'
    ],
    'qweb': [
        'static/src/xml/Popups/PromotionPopup.xml',
        'static/src/xml/Popups/ConfirmPaymentPopup.xml',
        'static/src/xml/Screens/ProductScreen/ProductScreen.xml',
        'static/src/xml/Screens/ProductScreen/PromotionContainer.xml',
        'static/src/xml/Screens/ProductScreen/PromotionList.xml',
        'static/src/xml/Screens/ProductScreen/PromotionItem.xml',
        'static/src/xml/Screens/ProductScreen/ControlButtons/ListPromotionButton.xml',
        'static/src/xml/Screens/ProductScreen/ControlButtons/ClearPromotionButton.xml',
        'static/src/xml/OrderLine.xml'
    ]
}

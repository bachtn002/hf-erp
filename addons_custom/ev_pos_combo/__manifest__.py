# -*- coding: utf-8 -*-
{
    'name': "ERPVIET POS Combo",
    'summary': """
        - Create Combo for POS Sale
        """,
    'description': """
        """,
    # TUUH
    'author': "ERPViet",
    'website': "https://erpviet.vn",
    'depends': ['base', 'point_of_sale', 'product', 'ev_pos_receipt'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/product_template.xml',
        'views/pos_config.xml',
        'views/orderline_combo.xml'
    ],
    'qweb': [
        'static/src/xml/*.xml',
        'static/src/xml/Popups/PopupCombo/*.xml',
        'static/src/xml/Screens/ProductScreen/*.xml',
        'static/src/xml/Screens/ReceiptScreen/*.xml',
    ],
}

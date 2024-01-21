# -*- coding: utf-8 -*-
{
    'name': "Return Products",

    'summary': """
        Returns products to Vendors and from Customers""",

    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'stock',
    'version': '0.1',
    'depends': ['base','account', 'purchase_stock', 'purchase','purchase_requisition'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/purchase_action.xml',
        #'views/sale_order_view.xml',
        #'views/sale_action.xml',
        'views/product_category.xml',
        'views/res_partner_views.xml',
        'views/stock_picking.xml',
        'views/account_move.xml',
        #'views/res_config_settings_views.xml',
        'report/bill_return_products_report.xml',
    ],
}
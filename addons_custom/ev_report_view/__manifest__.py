# -*- coding: utf-8 -*-
{
    'name': "Report view",

    'summary': """
        Report view""",

    'description': """
        Report view
    """,

    'author': "ERPVIET",
    'website': "https://erpviet.vn/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale', 'ev_pos_shop', 'account', 'ev_account_report_birt', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/bang_ke_chi_tiet_ban_hang_report_view.xml',
        'views/pre_tax_revenue_report_views.xml',
        'views/report_cash_statement.xml',
        'views/bang_tinh_khau_hao_tscd_view.xml',
        'views/theo_doi_tai_san_co_dinh_view.xml',
        'views/bang_tinh_ccdc_view.xml',
        'views/report_cash_statement.xml',
        'views/report_stock_transfer.xml',
        'views/report_stock_document.xml'
    ],
 
}

# -*- coding: utf-8 -*-
{
    'name': "ev_report_custom_v1",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'ev_report', 'ev_postgresql_materialized', 'ev_file_download',
                'account_reports', 'account', 'stock', 'ev_stock_report_birt', 'ev_pos_report', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        # 'data/bang_ke_mua_hang_data.xml',
        'data/bang_ke_chi_tiet_ban_hang_data.xml',
        # 'data/pre_tax_revenue_report_data.xml',
        # 'data/spreadsheet_depreciation_data.xml',
        # 'data/fixed_asset_tracking_report_data.xml',
        # 'data/fixed_asset_tracking_month_report_data.xml',
        # 'data/spreadsheet_tools_report_data.xml',
        # 'data/tools_tracking_report_data.xml',
        'data/stock_document_data.xml',
        # 'data/tools_tracking_month_report_data.xml',
        # 'data/stock_move_report_data.xml',
        'data/revenue_pos_payment_method_report_data.xml',
        'data/rpt_cash_statement_data.xml',
        'data/stock_transfer_report_data.xml',
        'views/menu_stock_report.xml',
        # 'wizard/bang_ke_mua_hang_report.xml',
        'wizard/bang_ke_chi_tiet_ban_hang_report.xml',
        # 'wizard/pre_tax_revenue_report_views.xml',
        # 'wizard/spreadsheet_depreciation_views.xml',
        # 'wizard/fixed_asset_tracking_report_views.xml',
        # 'wizard/fixed_asset_tracking_month_report_views.xml',
        # 'wizard/spreadsheet_tools_views.xml',
        # 'wizard/tools_tracking_report_views.xml',
        'wizard/stock_document_report_views.xml',
        # 'wizard/tools_tracking_month_report_views.xml',
        # 'wizard/stock_move_report_views.xml',
        'wizard/revenue_pos_payment_method_report_views.xml',
        'wizard/rpt_cash_statement_report.xml',
        'wizard/stock_transfer_report_views.xml',
    ],
}

# -*- coding: utf-8 -*-
{
    'name': "Account report birt",

    'summary': """
        Account report birt
        """,

    'description': """
        Account report birt
    """,

    'author': "ERPVIET",
    'website': "https://erpviet.vn/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/rpt_tong_hop_phat_sinh_cong_no.xml',
        'views/rpt_detail_debit_ncc.xml',
        'views/rpt_purchase_order.xml',
        'views/rpt_bang_ke_mua_hang.xml',
        'views/report_pos_payment_method.xml',
        'reports/report.xml',
        'views/account_financial_report.xml',
        'views/rpt_pre_tax_revenue.xml',
        'views/rpt_spreadsheet_depreciation.xml',
        'views/rpt_fixed_asset_tracking.xml',
        'views/rpt_fixed_asset_tracking_month.xml',
        'views/rpt_spreadsheet_tools.xml',
        'views/rpt_tools_tracking.xml',
        'views/rpt_tools_tracking_month.xml',
        'views/rpt_detailed_ledger.xml',
        'views/rpt_balances_arising.xml',
        'views/rpt_account_account.xml',
        'views/rpt_account_account_t.xml',
        'views/rpt_invoice_status.xml',
        'views/rpt_invoice_status.xml',
        'views/license_augment_reduce_no_warehosue.xml',
        'views/license_in_out_no_move.xml',
        'views/rpt_all_in_out_warehouse.xml',
        'views/rpt_all_in_out_move.xml',
        'views/rpt_account_journal_general.xml',
        'views/rpt_vat_out.xml',
        'views/rpt_vat_in.xml',
        'views/rpt_detail_by_product.xml',
        'views/rpt_detail_debit_by_account.xml',
    ],
}

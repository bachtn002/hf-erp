# -*- coding: utf-8 -*-
{
    'name': 'Accounting',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'sequence': 30,
    'summary': '',
    'description':
        """
        """,
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
    'depends': ['account', 'mail_community', 'web_tour'],
    'data': [
        'data/account_accountant_data.xml',
        'data/digest_data.xml',
        'security/ir.model.access.csv',
        'security/account_accountant_security.xml',
        'views/account_accountant_templates.xml',
        'views/account_account_views.xml',
        'views/account_bank_statement_views.xml',
        'views/account_fiscal_year_view.xml',
        'views/account_journal_dashboard_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/account_accountant_menuitems.xml',
        'views/digest_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'wizard/account_change_lock_date.xml',
        'wizard/reconcile_model_wizard.xml',
    ],
    'qweb': [
        "static/src/xml/account_reconciliation.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': '_account_accountant_post_init',
    'uninstall_hook': "uninstall_hook",
    'license': 'LGPL-3',
}
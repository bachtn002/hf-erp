# -*- coding: utf-8 -*-
{
    'name': 'Accounting Reports',
    'summary': '',
    'category': 'Accounting/Accounting',
    'description': """
    """,
    'depends': ['account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_financial_report_data.xml',
        'views/assets.xml',
        'views/account_report_view.xml',
        'views/report_financial.xml',
        'views/search_template_view.xml',
        'views/partner_view.xml',
        'views/account_journal_dashboard_view.xml',
        'views/res_config_settings_views.xml',
        'wizard/multicurrency_revaluation.xml',
        'wizard/report_export_wizard.xml',
        'wizard/fiscal_year.xml',
        'views/account_activity.xml',
    ],
    'qweb': [
        'static/src/xml/account_report_template.xml',
    ],
    'auto_install': True,
    'installable': True,
    'license': 'LGPL-3',
    'author': "ERPVIET",
    'website': 'https://www.erpviet.vn',
    'post_init_hook': 'set_periodicity_journal_on_companies',
}

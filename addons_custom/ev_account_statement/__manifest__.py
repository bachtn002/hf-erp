# -*- coding: utf-8 -*-
{
    'name': 'Account Statement',
    'version': '1.0',
    'category': 'Account Statement',
    'summary': 'ERPViet',
    'description': """
""",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",

    'depends': ['ev_account_erpviet', 'account', 'mail', 'report_xlsx', 'ev_pos_shop'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_statement_imp_view.xml',
        'views/account_statement.xml',
        'views/account_statement_line_view.xml',
        'report/report.xml',

    ],
    'installable': True,
}

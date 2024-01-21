# -*- coding: utf-8 -*-
{
    'name': "Account Posting",
    'summary': """
        Account in Vietnam
    """,
    'description': """
        Account in Vietnam
    """,
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['account','mail','ev_account_erpviet'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_posting_config_views.xml',
        'views/account_posting_views.xml',
        'data/data.xml',
    ],
}
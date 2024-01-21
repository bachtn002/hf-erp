# -*- coding: utf-8 -*-

{
    'name': 'Account Automatic Transfers',
    'depends': ['account_accountant'],
    'description': """
    """,
    'category': 'Accounting/Accounting',
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/transfer_model_views.xml',
    ],
    'application': False,
    'auto_install': True
}

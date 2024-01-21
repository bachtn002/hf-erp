# -*- coding: utf-8 -*-
{
    'name': "Account in Vietnam: Calculate cost of good",
    'summary': """
        + Calculate cost of goods \n 
    """,
    'description': """
        + Calculate cost of goods \n
    """,
    'author': "ERPVIET",
    'website': "http://www.erpviet.vn",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['ev_account_stock', 'ev_product_process', 'base', 'purchase','product'],
    'data': [
        'views/account_period_cost_views.xml',
        'data/account_period_cost_sequence.xml',
        # 'views/report_xlsx.xml',
        'views/product_product_view.xml',
        'security/ir.model.access.csv',
        'security/cost_price_security.xml',
        'security/ir_rule.xml',
    ],
}

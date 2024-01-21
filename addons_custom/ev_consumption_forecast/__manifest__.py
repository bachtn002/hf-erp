# -*- coding: utf-8 -*-
{
    'name': "Consumption Forecast",
    'summary': """
        Consumption Forecast Product
        """,
    'description': """
       Consumption Forecast Product
    """,
    'author': "ERPVIET",
    'website': "http://www.erpviet.vn",
    'category': 'Tools',
    'version': '0.1',
    'depends': ['base', 'ev_sale_request', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_request_notification.xml',
        'views/product_template.xml',
        'views/sale_request.xml',
        'views/request_forecast_daily.xml',
        'views/request_forecast_view.xml',
        'views/google_bigquery_config.xml',
        'views/stock_warehouse_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

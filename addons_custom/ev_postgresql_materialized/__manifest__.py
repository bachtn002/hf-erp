# -*- coding: utf-8 -*-
{
    'name': "EV PostgreSQL Materialized",
    'summary': """Module cung cấp công cụ tạo materialized nhanh tróng và đơn giản""",
    'description': """Module cung cấp công cụ tạo materialized nhanh tróng và đơn giản""",
    'author': "ERPViet",
    'website': "http://www.erpviet.vn",
    'category': 'Tools',
    'version': '6.0.0.1',
    'license': 'AGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/postgresql_materialized_cron.xml',
        'views/postgresql_materialized_views.xml'
    ]
}

# -*- coding: utf-8 -*-
{
    'name': "Excel Report, xlsx report - Report Design in Excel ",

    'summary': """
        Excel report, xlsx report - Use MS Excel to design reports
        """,

    'description': """
        The objective life of this module allows the user administration system to create the sample excel and export report in the simplest way, 
        the user administration system does not need to know odoo settings to still be able to generate the exported excel. 
        templates, excel reports according to your wishes.
    """,

    'author': "Dev Happy",
    'category': 'Tools',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/report_excel_template_views.xml',
        'wizards/report_excel_template_wizard.xml',
        'views/ir_actions_report_view.xml',
    ],
    'currency': 'EUR',
    'support':"dev.odoo.vn@gmail.com",
    'price': 199.99,
    'live_test_url':'https://youtu.be/Z1H5SY6F7Mg',
    'images':['static/description/banner.png'],
}

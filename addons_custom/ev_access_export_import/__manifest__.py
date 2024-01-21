# -*- coding: utf-8 -*-
{
    "name": "Access rules for Import/Export",
    "version": "0.1",
    "depends": ['web'],
    "author": "ERPViet",
    "license": 'AGPL-3',
    "description": """
Add access rules for import / export features
=============================================

For each user, you can indicate if it can export / import data

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "summary": "",
    "website": "http://www.izisolution.vn",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/web_impex_security.xml',
        'views/webclient_templates.xml',
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}

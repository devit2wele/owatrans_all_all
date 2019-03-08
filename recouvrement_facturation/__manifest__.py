# -*- coding: utf-8 -*-
{
    'name': 'Recouvrement Facturation Owatrans',
    'version': '1.0',
    'category': 'FACTURATION',
    'depends': [
        'base',
        'mail',
        'report'
    ],
    'description': """
        Long description of module's purpose
    """,
    'author': 'Aliou Samba WELE',
    'website': 'www.owatrans.sn',
    'license': 'AGPL-3',
    'data': [
        'security/recouvrement_facturation_security.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'views/owatrans_recouvrement_facturation_views.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
}
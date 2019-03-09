# -*- coding: utf-8 -*-
{
    'name': "Owatrans Parc Automobile",

    'description': """
        Owatrans entreprise : Gestion de parc automobile
    """,

    'author': "Abdou Mbar Ly",
    'website': "http://www.owatrans.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'fleet',
        'mail',
        'contacts',
        'hr'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/mail_template.xml',
        'data/ir_sequence_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
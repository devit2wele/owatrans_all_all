# -*- coding: utf-8 -*-
{
    'name': "Owatrans Bureau d'ordre",

    'description': """
        Owatrans entreprise : Gestions des imputations
    """,

    'author': "Abdou Mbar Ly",
    'website': "http://www.owatrans.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base' , 'hr'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/ir_sequence_data.xml',
        #'data/workflow.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
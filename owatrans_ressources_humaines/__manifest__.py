# -*- coding: utf-8 -*-
{
    'name': "Owatrans_Ressources_Humaines",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OWATRANS",
    'website': "http://www.owatrans.sn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'RH',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr',
        'hr_contract', 
        'hr_holidays',
        'report',
        'mail',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',   
        'data/fete_locale.xml', 
        'data/cron.xml',
        'views/owatrans_rh.xml',
        'views/import_historique_pointage_views.xml',
        'report/owatrans_rh_report.xml',
        'report/presence_template.xml',
        'data/template_mail.xml',
        
    ],
    
    'qweb' : [],

    
}

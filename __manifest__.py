# -*- coding: utf-8 -*-
{
    'name'     : 'InfoSaône - Module Odoo 12 pour Opta-S / SGP',
    'version'  : '0.1',
    'author'   : 'InfoSaône',
    'category' : 'InfoSaône',
    'description': """
InfoSaône - Module Odoo 12 pour Opta-S / SGP
===================================================
""",
    'maintainer' : 'InfoSaône',
    'website'    : 'http://www.infosaone.com',
    'depends'    : [
        'base',
        'account',
        'l10n_fr',
    ],
    'data' : [
        'security/res.groups.xml',
        'security/ir.model.access.csv',
        'security/ir.model.access.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/is_affaire_views.xml',
        'views/is_activite_views.xml',
        'views/is_suivi_temps_views.xml',
        'views/is_frais_views.xml',
        'views/account_invoice_view.xml',
        'views/is_activite_suivi_temps_views.xml',
        'views/menu.xml',
        'report/report_templates.xml',
        'report/report_invoice.xml',
    ],
    'installable': True,
    'application': True,
}

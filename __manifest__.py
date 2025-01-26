{
    'name': 'Warranty Tracker',
    'version': '1.0',
    "description": """
    This module is for  odoo-17 taining purposes 
    """,
    'depends': ['base', 'web', 'mail', "account",'hr', 'project'],
    "license": "LGPL-3",
    "author": "anowarul karim",
    'data': [
        'security/warranty_tracker_security.xml',
        'security/ir.model.access.csv',
        # 'data/warranty_data.xml',
        # 'data/warranty_claim_data.xml',
        'views/ir_sequence.xml',
        # 'data/warranty_products.csv',
        'data/warranty.product.csv',
        'views/warranty.xml',
        'wizard/warranty_report_wizard_view.xml',
        # 'wizard/warrnaty_report_wizard_view.xml',
        'views/res_config_settings.xml',
        'views/warranty_claim_views.xml',
        'views/warranty_tracker_menus.xml',
        'views/inherited_employe_view.xml',
    ],
    'application': True,
}

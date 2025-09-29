{
    'name': 'Request Installment Order',
    "version" : "17.0", 
    'category': 'Human Resources',
    'summary': 'Custom module for Order management',
    'description' :"""
        Modul custom untuk menambah fitur pada RIO
    """,
    "author": "Latip",
    'depends': ['base', 'hr', 'mail', 'account', 'base_geoengine'],   
    'data': [
        'security/ir.model.access.csv',
        'views/request_installment_order_views.xml',
        'views/request_installment_order_geoengine_views.xml',
        'views/geoengine_interactive_dashboard.xml',
        'views/menu_action.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # CSS Files
            'request_installment_order/static/src/css/map_styles.css',

            # JavaScript Files
            'request_installment_order/static/src/js/map_dashboard.js',
            'request_installment_order/static/src/js/map_picker_field.js',

            # XML Templates
            'request_installment_order/static/src/xml/map_picker_templates.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 50,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

}

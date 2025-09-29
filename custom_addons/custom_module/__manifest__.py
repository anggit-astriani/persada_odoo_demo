{
    'name': 'Custom Module',
    'version': '17.0.1.0',
    'category': 'Module',
    'summary': 'Custom Module',
    'description': """
        Custome Module by Anggit
    """,
    'website': '',
    'author': 'Anggit',
    'depends': ['web','base', 'product', 'account', 'purchase', 'mail', 'base_geoengine'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/return_product_wizard_view.xml',
        'views/menuitem_action.xml',
        'views/menuitem.xml',
        'views/stock_picking_view.xml',
        'views/checklist_instalasi_product_view.xml',
        'views/checklist_instalasi_lapangan_wizard_view.xml',
        'views/geoengine_delivered_order.xml',
        'views/geoengine_interactive_dashboard_view.xml',
        # 'views/customer_map_geoengine_views.xml',
        # 'views/anggit_purchase_view.xml',
        # 'views/anggit_purchase_action.xml',
        # 'views/anggit_purchase_menuitem.xml',
        # 'views/anggit_purchase_inv_sequence.xml',
        # 'views/res_config_settings_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # CSS Files
            'custom_module/static/src/css/map_styles.css',

            # JavaScript Files
            'custom_module/static/src/js/map_dashboard.js',
            'custom_module/static/src/js/map_picker_field.js',

            # XML Templates
            'custom_module/static/src/xml/map_picker_templates.xml',
        ],
    },
    'installable': True,
    'license': 'OEEL-1',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
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
    'depends': ['web','base', 'product', 'account', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/return_product_wizard_view.xml',
        'views/menuitem_action.xml',
        'views/menuitem.xml',
        'views/stock_picking_view.xml',
        'views/checklist_instalasi_product_view.xml',
        'views/checklist_instalasi_lapangan_wizard_view.xml'
        # 'views/anggit_purchase_view.xml',
        # 'views/anggit_purchase_action.xml',
        # 'views/anggit_purchase_menuitem.xml',
        # 'views/anggit_purchase_inv_sequence.xml',
        # 'views/res_config_settings_view.xml'
    ],
    'installable': True,
    'license': 'OEEL-1'
}
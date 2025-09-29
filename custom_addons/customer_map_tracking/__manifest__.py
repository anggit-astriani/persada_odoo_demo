# -*- coding: utf-8 -*-
{
    'name': 'Customer Map Tracking',
    'version': '1.0.0',
    'category': 'Extra Tools',
    'summary': 'Track customers / workers on map with PostGIS integration',
    'description': """
Customer Map Tracking with PostGIS
==================================

This module allows you to:
* Track customer locations using PostGIS geometry fields
* Set locations using geoengine map picker
* View all customers on a geoengine map
* Interactive JavaScript dashboard with Leaflet maps
* Full PostGIS integration like Field Service

Features:
* PostGIS geometry fields
* GeoEngine map views
* Interactive map editing
* Spatial queries support
* JavaScript dashboard with clustering
* Mobile-responsive design

Requirements:
* PostgreSQL with PostGIS extension
* base_geoengine module
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'base_geoengine',  # Required for PostGIS integration
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        # Security (must come first)
        'security/security.xml',
        'security/ir.model.access.csv',

        # Base Views (define views before referencing them)
        'views/customer_map_views.xml',
        'views/customer_map_geoengine_views.xml',

        # Actions (reference views defined above)
        'views/customer_map_actions.xml',

        # Menus (reference actions defined above) - Use safe menu file
        'views/customer_map_menus.xml',

        # Demo data (last)
        'demo/customer_map_demo.xml',
    ],
    'demo': [
        'demo/customer_map_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # CSS Files
            'customer_map_tracking/static/src/css/map_styles.css',

            # JavaScript Files
            'customer_map_tracking/static/src/js/map_dashboard.js',
            'customer_map_tracking/static/src/js/map_picker_field.js',

            # XML Templates
            'customer_map_tracking/static/src/xml/map_picker_templates.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 50,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
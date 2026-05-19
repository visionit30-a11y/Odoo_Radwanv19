# -*- coding: utf-8 -*-

{
    "name": "Radwan Helpdesk Branding",
    "version": "19.0.1.0.0",
    "summary": "Radwan visual identity for the helpdesk module without changing its technical links",
    "author": "Radwan",
    "category": "Services/Helpdesk",
    "depends": [
        "support_helpdesk_ticket",
        "radwan_helpdesk_menu_fix",
    ],
    "data": [
        "data/helpdesk_branding_data.xml",
        "data/helpdesk_performance_data.xml",
        "views/helpdesk_settings_branding_views.xml",
        "views/helpdesk_dashboard_branding_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_helpdesk_branding/static/src/css/helpdesk_branding.css",
            "radwan_helpdesk_branding/static/src/js/helpdesk_dashboard_classic_charts.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

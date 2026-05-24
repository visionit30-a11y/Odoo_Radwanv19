# -*- coding: utf-8 -*-

{
    "name": "Radwan Web UI Stability",
    "version": "19.0.1.3.0",
    "summary": "Small UI compatibility fixes for Radwan custom modules",
    "author": "Radwan",
    "category": "Technical",
    "depends": [
        "web",
        "hr",
        "hr_skills",
        "employee_orientation",
        "i8_knowledge_management",
        "mj_appraisal",
    ],
    "data": [
        "views/hr_development_menus.xml",
        "views/hr_contract_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_web_ui_stability/static/src/js/app_menu_groups.js",
            "radwan_web_ui_stability/static/src/js/skill_selection_highlight.js",
            "radwan_web_ui_stability/static/src/xml/app_menu_groups.xml",
            "radwan_web_ui_stability/static/src/css/search_panel_standard.css",
            "radwan_web_ui_stability/static/src/css/app_menu_groups.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

# -*- coding: utf-8 -*-

{
    "name": "Radwan HR AI Command Center",
    "version": "19.0.1.0.0",
    "summary": "HR AI command center for workforce insights and alerts",
    "description": "Management dashboard for HR AI insights, generated through the secure Radwan HR AI gateway.",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["radwan_hr_ai_employee"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_ai_command_center_views.xml",
        "views/hr_ai_command_menu_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}

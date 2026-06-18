# -*- coding: utf-8 -*-

{
    "name": "Radwan HR AI Employee Assistant",
    "version": "19.0.1.0.0",
    "summary": "Secure employee self-service AI assistant for HR data",
    "description": """
Secure HR AI layer for employees. The module reads HR data only through Odoo
ORM access rights and record rules, logs every question, and prepares an
AI-ready context without exposing unauthorized data.
""",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["hr", "mail", "website", "web"],
    "data": [
        "security/groups.xml",
        "security/rules.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/prompt_templates.xml",
        "data/default_training_knowledge.xml",
        "reports/hr_ai_employee_report.xml",
        "views/hr_ai_employee_views.xml",
        "views/hr_ai_data_access_views.xml",
        "views/hr_ai_provider_config_views.xml",
        "views/ai_training_knowledge_views.xml",
        "views/ai_training_test_wizard_views.xml",
        "views/hr_ai_portal_templates.xml",
        "views/hr_ai_menu_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}

# -*- coding: utf-8 -*-

{
    "name": "Radwan Appraisal Meal Base Compatibility",
    "version": "19.0.1.0.0",
    "summary": "Early meal.group model for appraisal compatibility",
    "description": """
Provides meal.group early in the module graph so mj_appraisal meal wizards can
be registered reliably on Odoo 19.
""",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

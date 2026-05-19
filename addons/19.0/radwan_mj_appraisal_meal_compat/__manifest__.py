# -*- coding: utf-8 -*-

{
    "name": "Radwan Appraisal Meal Compatibility",
    "version": "19.0.1.0.0",
    "summary": "Compatibility prerequisite for the appraisal module on Odoo 19",
    "description": """
Keeps compatibility metadata around the early meal.group base model required
by the third-party mj_appraisal module during registry setup.
""",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["a_radwan_mj_appraisal_meal_base"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

# -*- coding: utf-8 -*-

{
    "name": "Radwan Appraisal Stability",
    "version": "19.0.1.0.0",
    "summary": "Stability fixes for Performance Appraisal on Odoo 19",
    "description": """
Keeps the third-party Performance Appraisal module aligned with Odoo 19 by
scoping access rights and accepting legacy field parameters used by the module.
""",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["mj_appraisal"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

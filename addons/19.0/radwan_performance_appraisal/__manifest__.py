# -*- coding: utf-8 -*-
{
    "name": "Radwan Performance Appraisal",
    "version": "19.0.1.0.1",
    "summary": "Employee performance appraisal workflow for Radwan HR",
    "description": """
        Performance appraisal management for employees, including appraisal
        types, periods, criteria, templates, approval stages, ratings, and
        weighted score calculations.
    """,
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["hr", "mail"],
    "data": [
        "security/appraisal_security.xml",
        "security/ir.model.access.csv",
        "data/appraisal_sequence_data.xml",
        "data/appraisal_rating_data.xml",
        "data/appraisal_type_data.xml",
        "data/appraisal_criteria_data.xml",
        "views/appraisal_rating_views.xml",
        "views/appraisal_type_views.xml",
        "views/appraisal_period_views.xml",
        "views/appraisal_criteria_views.xml",
        "views/appraisal_template_views.xml",
        "views/appraisal_views.xml",
        "views/appraisal_menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "sequence": 85,
}

# -*- coding: utf-8 -*-

{
    "name": "Radwan Time Off Custom",
    "summary": "Configure weekly off day calculation in time off durations",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Time Off",
    "author": "Radwan",
    "license": "LGPL-3",
    "depends": ["hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_leave_type_views.xml",
    ],
    "installable": True,
    "application": False,
}

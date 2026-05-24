# -*- coding: utf-8 -*-

{
    "name": "Radwan HR Employee Custom Fields",
    "version": "19.0.1.4.0",
    "summary": "Custom fields for employee profile in Odoo 19 Community",
    "description": "Custom HR fields, expiry statuses, Hijri/Gregorian conversion, and ID/Iqama validations.",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["hr"],
    "data": [
        "data/ir_cron.xml",
        "views/hr_employee_views.xml",
        "views/expiry_monitoring_views.xml",
        "reports/employee_reports.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_hr_employee_custom/static/src/scss/hr_employee_rtl.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}

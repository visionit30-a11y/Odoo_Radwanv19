# -*- coding: utf-8 -*-

{
    "name": "Radwan Report PDF Options Context Fix",
    "version": "19.0.1.0.0",
    "summary": "Preserve user context when report_pdf_options opens or prints PDF reports",
    "author": "Radwan",
    "category": "Reporting",
    "depends": ["report_pdf_options", "om_hr_payroll"],
    "data": [
        "data/payroll_report_options_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_report_pdf_options_context_fix/static/src/js/qwebactionmanager_context_fix.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

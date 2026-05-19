# -*- coding: utf-8 -*-

{
    "name": "Radwan Contract Payroll Customization",
    "version": "19.0.1.0.0",
    "summary": "Custom payroll fields on contract templates and employee versions",
    "author": "Radwan",
    "category": "Human Resources",
    "depends": ["hr", "om_hr_payroll"],
    "data": [
        "data/radwan_payroll_data.xml",
        "views/hr_contract_template_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_contract_payroll_custom/static/src/scss/contract_payroll_custom.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}

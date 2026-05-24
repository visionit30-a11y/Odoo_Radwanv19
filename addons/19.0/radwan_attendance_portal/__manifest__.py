# -*- coding: utf-8 -*-

{
    "name": "Radwan Attendance Portal",
    "version": "19.0.1.2.6",
    "summary": "Employee attendance portal with GPS check in and check out",
    "author": "Radwan",
    "category": "Human Resources/Attendances",
    "depends": [
        "hr_attendance",
        "portal",
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/radwan_attendance_portal_templates.xml",
        "views/radwan_attendance_portal_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "radwan_attendance_portal/static/src/scss/radwan_attendance_portal.scss",
            "radwan_attendance_portal/static/src/js/radwan_attendance_portal.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

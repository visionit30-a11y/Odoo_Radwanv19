# -*- coding: utf-8 -*-

{
    "name": "Radwan Documents Employee Link",
    "version": "19.0.1.0.0",
    "summary": "Link custom documents to employees and partners",
    "author": "Radwan",
    "category": "Productivity/Documents",
    "depends": ["document_management_system", "hr"],
    "data": [
        "views/document_document_views.xml",
        "views/hr_employee_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_document_employee_link/static/src/js/document_attachment_preview.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

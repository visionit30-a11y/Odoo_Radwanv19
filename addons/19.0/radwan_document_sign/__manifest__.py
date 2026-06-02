# -*- coding: utf-8 -*-

{
    "name": "Radwan Document E-Signature",
    "version": "19.0.1.0.0",
    "summary": "Request and capture electronic signatures for Radwan documents",
    "author": "Radwan",
    "category": "Productivity/Documents",
    "depends": [
        "portal",
        "mail",
        "document_management_system",
        "radwan_document_employee_link",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/document_sign_request_views.xml",
        "views/document_document_views.xml",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

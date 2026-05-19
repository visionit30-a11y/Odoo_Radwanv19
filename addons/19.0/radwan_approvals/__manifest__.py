{
    "name": "Radwan Approvals",
    "version": "19.0.1.1.0",
    "category": "Human Resources",
    "summary": "Create and validate approval requests",
    "description": """
Radwan Approvals
================

Manage approval requests with configurable approval types, approvers,
activities, products, attachments, and manager review screens.
    """,
    "author": "AL RADWAN IT SOLUTIONS",
    "website": "https://www.alradwan.local",
    "license": "LGPL-3",
    "depends": ["hr", "mail", "product"],
    "data": [
        "security/radwan_approvals_groups.xml",
        "security/ir.model.access.csv",
        "security/radwan_approvals_security.xml",
        "data/ir_sequence_data.xml",
        "data/approval_category_data.xml",
        "views/approval_category_views.xml",
        "views/approval_request_views.xml",
        "views/approval_product_line_views.xml",
        "views/approval_menus.xml",
    ],
    "application": True,
    "installable": True,
}

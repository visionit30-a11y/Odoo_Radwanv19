{
    "name": "Radwan User Audit Stability",
    "summary": "Stabilize user audit references and multi-company sequence usage.",
    "version": "19.0.1.0.0",
    "category": "Extra Tools",
    "author": "Radwan",
    "license": "LGPL-3",
    "depends": ["user_audit"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "radwan_user_audit_stability/static/src/js/audit_non_blocking.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}

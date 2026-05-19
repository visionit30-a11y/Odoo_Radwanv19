{
    "name": "Radwan Report Speed Fix",
    "version": "19.0.1.0.0",
    "summary": "Reduce wkhtmltopdf delays on local Windows Odoo reports",
    "author": "Radwan",
    "category": "Technical",
    "depends": ["web"],
    "data": [
        "data/report_config_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "radwan_report_speed_fix/static/src/js/report_preview_first.js",
        ],
        "web.report_assets_common": [
            "radwan_report_speed_fix/static/src/scss/report_no_external_fonts.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}

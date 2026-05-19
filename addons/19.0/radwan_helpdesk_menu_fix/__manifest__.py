# -*- coding: utf-8 -*-

{
    "name": "Radwan Helpdesk Menu Fix",
    "version": "19.0.1.0.0",
    "summary": "Expose the installed helpdesk app menu to the proper Odoo user groups",
    "author": "Radwan",
    "category": "Services/Helpdesk",
    "depends": ["support_helpdesk_ticket"],
    "data": [
        "data/helpdesk_menu_security_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}

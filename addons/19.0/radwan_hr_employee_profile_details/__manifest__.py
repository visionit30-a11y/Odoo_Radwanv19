{
    "name": "Radwan HR Employee Profile Details",
    "summary": "Adds sponsor, document dates, and family details to employee profiles.",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "author": "Radwan",
    "license": "LGPL-3",
    "depends": [
        "radwan_hr_employee_custom_stability",
        "radwan_contract_payroll_custom",
        "employee_orientation",
        "hr_homeworking",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/radwan_employee_sponser_data.xml",
        "views/radwan_employee_sponser_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_employee_collapsible_views.xml",
        "views/expiry_monitoring_views.xml",
    ],
    "installable": True,
    "application": False,
}

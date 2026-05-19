{
    'name': 'Employee Loan Management',
    'summary': 'Manage employee loans and integrate installments with payroll',
    'description': """
Employee Loan Management
========================

Manage employee loans, installment schedules, accounting entries, and payroll
deductions through standard Odoo models.
    """,
    'author': 'RADWAN',
    'website': 'https://www.radwan.local',
    'category': 'Human Resources',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'hr',
        'mail',
        'om_hr_payroll',
        'om_hr_payroll_account',
    ],
    'data': [
        'security/radwan_hr_loan_groups.xml',
        'security/ir.model.access.csv',
        'security/radwan_hr_loan_security.xml',
        'data/hr_loan_sequence.xml',
        'data/hr_loan_data.xml',
        'report/hr_loan_reports.xml',
        'report/hr_loan_templates.xml',
        'wizard/hr_loan_payment_wizard_views.xml',
        'wizard/hr_loan_report_wizard_views.xml',
        'views/hr_loan_payment_method_views.xml',
        'views/hr_loan_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_loan_menus.xml',
    ],
    'application': True,
    'installable': True,
}

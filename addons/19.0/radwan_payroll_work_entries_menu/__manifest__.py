{
    'name': 'Radwan Payroll Work Entries Menu',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Show work entries inside Payroll menus',
    'author': 'RADWAN',
    'license': 'LGPL-3',
    'depends': [
        'om_hr_payroll',
        'hr_work_entry',
    ],
    'data': [
        'views/hr_work_entry_menus.xml',
    ],
    'application': False,
    'installable': True,
}

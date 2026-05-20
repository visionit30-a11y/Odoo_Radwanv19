{
    'name': 'Radwan Project Planning',
    'summary': "Manage employees' schedules and project resource planning.",
    'version': '19.0.1.0.0',
    'category': 'Services/Project',
    'author': 'Radwan',
    'license': 'LGPL-3',
    'depends': [
        'base_setup',
        'digest',
        'hr_hourly_cost',
        'project',
        'hr_timesheet',
        'resource',
        'mail',
    ],
    'data': [
        'security/radwan_project_planning_groups.xml',
        'security/ir.model.access.csv',
        'security/radwan_project_planning_security.xml',
        'data/radwan_project_planning_sequence.xml',
        'views/radwan_planning_role_views.xml',
        'views/radwan_planning_material_views.xml',
        'views/radwan_planning_template_views.xml',
        'views/radwan_planning_slot_views.xml',
        'views/hr_employee_views.xml',
        'views/project_project_views.xml',
        'views/account_analytic_line_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/radwan_planning_generate_wizard_views.xml',
        'views/radwan_planning_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'radwan_project_planning/static/src/js/planning_gantt_action.js',
            'radwan_project_planning/static/src/xml/planning_gantt_action.xml',
            'radwan_project_planning/static/src/scss/planning_gantt.scss',
        ],
    },
    'description': """
Schedule employees, open shifts, material resources, and project work while
keeping planned hours connected to timesheets and project analysis.
""",
    'installable': True,
    'application': True,
}

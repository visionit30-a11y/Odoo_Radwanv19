{
    "name": "Radwan Job Description",
    "summary": "Structured job descriptions for recruitment job positions.",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Recruitment",
    "author": "Radwan",
    "license": "LGPL-3",
    "depends": [
        "hr_recruitment",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/radwan_job_description_section_data.xml",
        "views/radwan_job_description_section_views.xml",
        "views/hr_job_views.xml",
    ],
    "installable": True,
    "application": False,
}

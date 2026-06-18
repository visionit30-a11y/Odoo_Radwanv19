# -*- coding: utf-8 -*-
{
    'name': 'تقييم الأداء',
    'version': '19.0.1.0.0',
    'summary': 'نظام متكامل لتقييم أداء الموظفين بأنواعه ومراحله وفتراته',
    'description': '''
        نظام تقييم الأداء المخصص:
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        • أنواع التقييم (سنوي، نصف سنوي، ربعي، اختباري، خاص)
        • فترات التقييم بتواريخ محددة ودورة حياة (مسودة ← مفتوحة ← مغلقة)
        • معايير التقييم بأوزان وفئات متعددة
        • قوالب التقييم القابلة للتخصيص حسب نوع التقييم
        • مراحل الموافقة المتسلسلة (ذاتي → مدير → موارد بشرية → مكتمل)
        • مقياس التقييم والتقدير (ممتاز / جيد جداً / جيد / مقبول / ضعيف)
        • حساب تلقائي للدرجات الموزونة والإجمالية
        • تقارير وإحصاءات شاملة
    ''',
    'author': 'Radwan',
    'category': 'Human Resources',
    'depends': ['hr', 'mail'],
    'data': [
        'security/appraisal_security.xml',
        'security/ir.model.access.csv',
        'data/appraisal_sequence_data.xml',
        'data/appraisal_rating_data.xml',
        'data/appraisal_type_data.xml',
        'data/appraisal_criteria_data.xml',
        'views/appraisal_rating_views.xml',
        'views/appraisal_type_views.xml',
        'views/appraisal_period_views.xml',
        'views/appraisal_criteria_views.xml',
        'views/appraisal_template_views.xml',
        'views/appraisal_views.xml',
        'views/appraisal_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 85,
}

# -*- coding: utf-8 -*-

from . import models


def post_init_hook(env):
    group_user = env.ref("base.group_user", raise_if_not_found=False)
    if not group_user:
        return

    access_xmlids = [
        "mj_appraisal.access_performance_appraisal",
        "mj_appraisal.access_performance_appraiser",
        "mj_appraisal.access_performance_appraiser_line",
        "mj_appraisal.access_performance_evaluation_topic",
    ]
    for xmlid in access_xmlids:
        access = env.ref(xmlid, raise_if_not_found=False)
        if access and not access.group_id:
            access.group_id = group_user

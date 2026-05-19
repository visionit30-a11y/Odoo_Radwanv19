from . import models


def post_init_hook(env):
    env["user.audit.log"]._radwan_prepare_audit_sequence()

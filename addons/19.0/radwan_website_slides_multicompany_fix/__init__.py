from . import models


def post_init_hook(env):
    env["slide.channel"]._radwan_normalize_learning_partner_companies()

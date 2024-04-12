# pylint: disable=C0116
from random import randint

from odoo import fields, models


def _get_default_color():
    return randint(1, 11)


class UpgradePlanTags(models.Model):
    _name = "upgrade.plan.tags"
    _description = "Upgrade Plan Tags"

    name = fields.Char(
        required=True,
    )
    code = fields.Char()
    active = fields.Boolean(default=True)
    color = fields.Integer(
        string="Color Index",
        default=_get_default_color,
    )

# pylint: disable=C0116
from random import randint

from odoo import fields, models


class UpgradePlanTags(models.Model):
    _name = "upgrade.plan.tags"
    _description = "Upgrade Plan Tags"

    def _get_default_color(self):  # pylint: disable=R0201
        return randint(1, 11)

    name = fields.Char(
        required=True,
        translate=True,
    )
    code = fields.Char()
    active = fields.Boolean(default=True)
    color = fields.Integer(
        string="Color Index",
        default=_get_default_color,
    )

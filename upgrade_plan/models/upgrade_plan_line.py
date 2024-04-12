# pylint: disable=C0103,C0116
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

FEATURE_FORMAT = "\tFeature: {}".format


class UpgradePlanLine(models.Model):
    _name = "upgrade.plan.line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Upgrade Plan Line"

    name = fields.Char(
        required=True,
    )
    technical_name = fields.Char()
    active = fields.Boolean(
        default=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )

    description = fields.Text()
    note = fields.Html()
    author = fields.Char()
    category = fields.Char()
    repository = fields.Char()
    url = fields.Char()
    version = fields.Char()
    upgrade_id = fields.Many2one(
        comodel_name="upgrade.plan",
        required=True,
        ondelete="cascade",
    )
    project_id = fields.Many2one(
        related="upgrade_id.project_id",
    )
    reviewer = fields.Many2one(
        comodel_name="res.users",
    )
    tag_ids = fields.Many2many(
        comodel_name="upgrade.plan.tags",
        relation="upgrade_plan_line_tags_rel",
        string="Tags",
    )
    parent_id = fields.Many2one(
        comodel_name="upgrade.plan.line", compute="_compute_parent"
    )

    available = fields.Boolean(
        default=False,
        tracking=True,
    )
    review = fields.Boolean(
        default=False,
        tracking=True,
    )
    to_review = fields.Boolean(
        compute="_compute_review",
    )
    need_action = fields.Boolean(
        compute="_compute_review",
    )

    action = fields.Selection(
        selection=[
            ("drop", "Drop"),
            ("keep", "Keep"),
            ("migrate", "Migrate"),
            ("install", "Install"),
        ],
        string="Action",
        copy=False,
        index=True,
        tracking=3,
        default=False,
    )

    review_date = fields.Datetime()
    duration = fields.Float()

    display_type = fields.Selection(
        selection=[
            ("line_section", "Section"),
            ("line_note", "Note"),
        ],
        default=False,
    )

    line_type = fields.Selection(
        selection=[
            ("module", "Module"),
            ("feature", "Feature"),
        ],
        default=False,
    )

    @api.depends("action", "review")
    def _compute_review(self):
        for record in self:
            record.to_review = (
                record.line_type == "module" and record.action and not record.review
            )
            record.need_action = (
                record.line_type == "module" and not record.action and not record.review
            )

    @api.depends("sequence")
    def _compute_parent(self):
        for record in self:
            if record.line_type != "feature":
                record.parent_id = False

            data = (
                record.upgrade_id.lines.filtered_domain(
                    [("sequence", "<=", record.sequence)]
                )
                .sorted("sequence", reverse=False)
                .read(["sequence", "line_type", "upgrade_id"])
            )

            res = [(item["line_type"], item["id"]) for item in data]

            parent_id = False

            for line_type, id in res:  # pylint: disable=W0622
                if not line_type:
                    continue
                if line_type == "module":
                    parent_id = id
                    continue

            _logger.warning(res)

            record.parent_id = parent_id

    def guess_repository(self):
        for record in self.filtered(lambda item: item.url and not item.repository):
            if "github.com/OCA" in record.url:
                record.repository = record.url.split("/")[-1]

    def action_validate(self):
        self.write(
            {
                "review": True,
                "reviewer": self.env.user.id,
                "review_date": fields.Datetime.now(),
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        # number = 1
        for vals in vals_list:
            if vals.get("line_type") == "feature":
                name = vals.get("name")
                vals["name"] = FEATURE_FORMAT(name)

                # vals["name"] = f"\tFeature-{number}: {name}"
                # number += 1

        return super().create(vals_list)

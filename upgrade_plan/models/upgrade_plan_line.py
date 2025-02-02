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

    parent_id = fields.Many2one(
        comodel_name="upgrade.plan.line",
        string="Module",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        comodel_name="upgrade.plan.line",
        inverse_name="parent_id",
        string="Features",
    )

    description = fields.Text()
    note = fields.Html()
    author = fields.Char()
    category = fields.Char()
    repository = fields.Char()
    url = fields.Char()
    version = fields.Char()
    plan_id = fields.Many2one(
        comodel_name="upgrade.plan",
        required=True,
        ondelete="cascade",
    )
    project_id = fields.Many2one(
        related="plan_id.project_id",
    )
    reviewer = fields.Many2one(
        comodel_name="res.users",
    )
    tag_ids = fields.Many2many(
        comodel_name="upgrade.plan.tags",
        relation="upgrade_plan_line_tags_rel",
        string="Tags",
    )
    # parent_id = fields.Many2one(
    #     comodel_name="upgrade.plan.line",
    #     compute="_compute_parent",
    # )
    available = fields.Boolean(
        default=False,
        tracking=True,
    )
    review = fields.Boolean(
        default=False,
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

    # @api.depends("sequence")
    # def _compute_parent(self):
    #     for record in self:
    #         if record.line_type != "feature":
    #             record.parent_id = False

    #         data = (
    #             record.plan_id.line_ids.filtered_domain(
    #                 [("sequence", "<=", record.sequence)]
    #             )
    #             .sorted("sequence", reverse=False)
    #             .read(["sequence", "line_type", "plan_id"])
    #         )

    #         res = [(item["line_type"], item["id"]) for item in data]

    #         parent_id = False

    #         for line_type, id in res:  # pylint: disable=W0622
    #             if not line_type:
    #                 continue
    #             if line_type == "module":
    #                 parent_id = id
    #                 continue

    #         _logger.warning(res)

    #         record.parent_id = parent_id

    @api.depends("name", "line_type")
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"Module - {record.name}"
                if record.line_type == "module"
                else record.name
            )

    def action_validate(self):
        self.write(
            {
                "review": True,
                "reviewer": self.env.user.id,
                "review_date": fields.Datetime.now(),
            }
        )

    def action_cancel(self):
        self.write(
            {
                "review": False,
                "reviewer": False,
                "review_date": False,
            }
        )

    def action_view_plan(self):
        self.ensure_one()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "upgrade_plan.action_view_upgrade_plan"
        )
        action.update(
            {
                "view_mode": "form",
                "res_id": self.plan_id.id,
                "views": [
                    (view_id, view_type)
                    for view_id, view_type in action["views"]
                    if view_type == "form"
                ],
            }
        )
        return action

    def guess_repository(self):
        for record in self.filtered(lambda item: item.url and not item.repository):
            if "github.com/OCA" in record.url:
                record.repository = record.url.split("/")[-1]

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

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self.parent_id:
            self.sequence = self.parent_id.sequence + 1

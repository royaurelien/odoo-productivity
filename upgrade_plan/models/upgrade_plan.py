# pylint: disable=C0103,C0116
import ast

from odoo import _, api, fields, models
from odoo.exceptions import UserError

UPGRADE_PLAN_STATE = [
    ("draft", "Draft"),
    ("progress", "In Progress"),
    ("done", "Validated"),
    ("cancel", "Cancelled"),
]


class UpgradePlan(models.Model):
    _name = "upgrade.plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Upgrade Plan"

    name = fields.Char(
        required=True,
        index=True,
    )
    active = fields.Boolean(
        default=True,
    )
    description = fields.Text()
    version = fields.Integer(
        string="Revision",
        default=1,
        readonly=True,
    )
    previous_plan_id = fields.Many2one(
        comodel_name="upgrade.plan",
        string="Previous Plan",
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned to",
        tracking=True,
    )
    from_version = fields.Char(
        required=True,
        string="From",
    )
    to_version = fields.Char(
        required=True,
        string="To",
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        required=True,
    )
    partner_id = fields.Many2one(
        related="project_id.partner_id",
        store=True,
    )
    line_ids = fields.One2many(
        comodel_name="upgrade.plan.line",
        inverse_name="plan_id",
        copy=True,
    )

    modules = fields.One2many(
        comodel_name="upgrade.plan.line",
        inverse_name="plan_id",
        domain=[("line_type", "=", "module")],
    )

    features = fields.One2many(
        comodel_name="upgrade.plan.line",
        inverse_name="plan_id",
        domain=[("line_type", "=", "feature")],
    )

    module_count = fields.Integer(
        compute="_compute_progress",
        string="# Modules",
    )
    feature_count = fields.Integer(
        compute="_compute_features",
        string="# Features",
    )
    to_review = fields.Integer(
        compute="_compute_progress",
    )
    progress = fields.Float(
        compute="_compute_progress",
        group_operator="avg",
    )
    is_complete = fields.Integer(
        compute="_compute_progress",
    )

    state = fields.Selection(
        selection=UPGRADE_PLAN_STATE,
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default="draft",
    )
    locked = fields.Boolean(
        default=False,
        copy=False,
        help="Locked plans cannot be modified.",
    )
    total_duration = fields.Float(
        compute="_compute_duration",
        store=True,
    )

    @api.depends("line_ids.duration")
    def _compute_duration(self):
        for record in self:
            record.total_duration = sum(record.line_ids.mapped("duration"))

    @api.depends("modules", "modules.review")
    def _compute_progress(self):
        for record in self:
            total = len(record.modules)
            to_review = total - len(
                record.modules.filtered(lambda item: not item.review)
            )
            record.progress = (
                round(100.0 * to_review / total, 2) if to_review > 0.0 else 0.0
            )
            record.module_count = total
            record.to_review = to_review
            record.is_complete = total and (total == to_review)

    @api.depends("features")
    def _compute_features(self):
        for record in self:
            record.feature_count = len(record.features)

    def action_unlock(self):
        self.locked = False

    def action_lock(self):
        self.locked = True

    def action_validate(self):
        self.state = "done"

    def action_cancel(self):
        self.state = "cancel"

    def action_draft(self):
        self.state = "draft"

    def action_progress(self):
        self.state = "progress"

    def action_guess_repositories(self):
        self.ensure_one()

        self.modules.guess_repository()

    def action_generate_tasks(self):
        raise UserError(
            _(
                "Sorry, this feature isn't implemented, but you can buy me a coffee and I'll take care of it!"
            )
        )

    def action_view_modules(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "upgrade_plan.action_view_upgrade_plan_line"
        )
        action.update(
            {
                "domain": [
                    ("id", "in", self.modules.ids),
                ],
                "context": {
                    "default_plan_id": self.id,
                    "default_line_type": "module",
                    "create": not self.locked,
                    "delete": not self.locked,
                    "edit": not self.locked,
                },
            }
        )
        return action

    def action_view_features(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "upgrade_plan.action_view_upgrade_plan_line"
        )

        action.update(
            {
                "domain": [
                    ("id", "in", self.features.ids),
                ],
                "context": {
                    "default_plan_id": self.id,
                    "default_line_type": "feature",
                    "create": not self.locked,
                    "delete": not self.locked,
                    "edit": not self.locked,
                },
                "views": [
                    [
                        self.env.ref(
                            "upgrade_plan.view_upgrade_plan_line_tree_feature"
                        ).id,
                        "tree",
                    ]
                ],
            }
        )

        return action

    def action_new_revision(self):
        self.ensure_one()

        IrAttachment = self.env["ir.attachment"]
        for record in self:
            new_plan = record.sudo().copy(
                default={
                    "version": record.version + 1,
                    "active": True,
                    "previous_plan_id": record.id,
                }
            )
            attachments = IrAttachment.search(
                [("res_model", "=", "upgrade.plan"), ("res_id", "=", record.id)]
            )

            for attach in attachments:
                attach.copy({"res_model": "upgrade.plan", "res_id": new_plan.id})
                # self.env["mrp.document"].create(
                #     {
                #         "ir_attachment_id": new_attach.id,
                #         "origin_attachment_id": attach.id,
                #     }
                # )
        self.write(
            {
                "state": "progress",
                "locked": True,
                "active": False,
            }
        )

        action = self.env["ir.actions.actions"]._for_xml_id(
            "upgrade_plan.action_view_upgrade_plan"
        )
        action.update(
            {
                "domain": [],
                "context": {
                    **ast.literal_eval(action.get("context", {})),
                    "create": False,
                },
                "view_mode": "form",
                "res_id": new_plan.id,
                "views": [
                    (view_id, view_type)
                    for view_id, view_type in action["views"]
                    if view_type == "form"
                ],
            }
        )
        return action

    @api.depends("name", "version")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} (rev:{record.version})"

# pylint: disable=C0103,C0116

from odoo import api, fields, models

CUSTOM_FIELDS = ["subject", "flux", "implementation"]


class ProjectTask(models.Model):
    _inherit = "project.task"

    subject = fields.Char(
        readonly=False,
        copy=True,
    )
    flux = fields.Char(
        readonly=False,
        default="master",
        copy=True,
    )
    implementation = fields.Char(
        readonly=False,
        copy=True,
    )

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self.parent_id:
            self.flux = self.parent_id.flux if self.parent_id.flux else False
            self.subject = self.parent_id.subject if self.parent_id.subject else False
            self.implementation = (
                self.parent_id.implementation
                if self.parent_id.implementation
                else False
            )

    @api.model
    def _get_gap2_description(self, data):
        return self.env["ir.qweb"]._render(
            "project_task_import_gap.gap2_description",
            {"data": data},
        )

    @api.model
    def _prepare_from_gap2(self, data):
        name = eval('f"{}"'.format(data["name"]))  # pylint: disable=W0123,C0209
        vals = {
            "name": name,
            "allocated_hours": data.get("Total", 0.0) * 7,
            "description": self._get_gap2_description(data),
            "flux": data.get("Flux", ""),
            "subject": data.get("Sujet", ""),
            "tag_ids": data.get("tag_ids", False),
            "parent_id": data.get("parent_id", False),
            "implementation": data.get("Implémentation"),
        }
        return vals

    def _get_custom_values(self):
        return {field: getattr(self, field) for field in CUSTOM_FIELDS}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            parent_id = vals.get("parent_id")
            if parent_id:
                parent = self.browse(parent_id)
                vals.update(parent._get_custom_values())

        return super().create(vals_list)

# pylint: disable=C0103,C0116

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    subject = fields.Char(
        readonly=True,
    )
    flux = fields.Char(
        readonly=True,
    )

    @api.model
    def _get_description(self, data):
        return self.env["ir.qweb"]._render(
            "project_task_import_gap.gap2_description",
            {"data": data},
        )

    @api.model
    def _prepare_from_gap2(self, data):
        vals = {
            "name": f"{data['Sujet']}: {data['Description précise fonctionnelle']}",
            "allocated_hours": data.get("Total", 0.0) * 7,
            "description": self._get_description(data),
            "flux": data.get("Flux", ""),
            "subject": data.get("Sujet", ""),
            "tag_ids": data.get("tag_ids", False),
            "parent_id": data.get("parent_id", False),
        }
        return vals

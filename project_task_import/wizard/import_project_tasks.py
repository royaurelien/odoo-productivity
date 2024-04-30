import logging
import mimetypes
from base64 import b64decode
from io import BytesIO

import openpyxl

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportProjectTasks(models.TransientModel):
    _name = "import.project.tasks"
    _description = "Import Project Tasks"

    template = fields.Selection(
        selection=[],
        default=None,
        help="Select a type which you want to import",
    )
    import_file = fields.Binary(
        string="File",
        required=True,
        help="Upload a file. Supported formats: Xlsx.",
    )
    import_filename = fields.Char(
        string="Filename",
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        required=True,
    )
    use_subtasks = fields.Boolean(
        default=False,
    )
    parent_key = fields.Char()
    locked = fields.Boolean(
        default=False,
    )
    task_name = fields.Char()
    sheets = fields.Char()
    sheets_to_import = fields.Char()

    def _get_supported_types(self):
        # Define the supported types dictionary
        supported_types = {
            "xlsx": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "xls": ("application/vnd.ms-excel"),
        }
        return supported_types

    @api.model
    def _get_workbook(self, filecontent):
        return openpyxl.load_workbook(BytesIO(filecontent), read_only=True)

    def _parse_file(self, filename, filecontent):
        assert filename, "Missing filename"
        assert filecontent, "Missing file content"

        filetype = mimetypes.guess_type(filename)
        mimetype = filetype[0]
        supported_types = self._get_supported_types()

        workbook = self._get_workbook(filecontent)

        # Check if the detected MIME type is supported for the selected import type
        if mimetype not in supported_types["xlsx"]:
            raise UserError(
                _(
                    "This file '%(filename)s' is not recognized as a %(type)s file. "
                    "Please check the file and its extension.",
                    filename=filename,
                    type=mimetype,
                )
            )
        if hasattr(self, f"parse_{self.template}"):
            return getattr(self, f"parse_{self.template}")(workbook)

        raise UserError(
            _(
                "This Import Type is not supported. Did you install "
                "the module to support this type?"
            )
        )

    @api.onchange("template")
    def _onchange_subtasks(self):
        if not self.use_subtasks:
            self.parent_key = ""

        if not self.template:
            self.import_file = False
            self.import_filename = False

    @api.onchange("import_file")
    def _onchange_import_file(self):
        if not self.import_filename or not self.import_file:
            self.sheets = False
            return

        workbook = self._get_workbook(b64decode(self.import_file))
        sheets = workbook.sheetnames

        if sheets is None:
            return {"warning": "No sheets found !"}

        self.sheets = ",".join(sheets)

    def import_button(self):
        self.ensure_one()

        file_decoded = b64decode(self.import_file)
        tasks = self._parse_file(
            self.import_filename,
            file_decoded,
        )
        if not tasks:
            raise UserError(_("This order doesn't have any line !"))

        Task = self.env["project.task"].sudo()
        Task.create_from_import(tasks, self.project_id.id, self.import_filename)

        action = self.env["ir.actions.actions"]._for_xml_id(
            "project.act_project_project_2_project_task_all"
        )
        action.update(
            {
                "context": {},
                "domain": [
                    ("project_id", "=", self.project_id.id),
                    ("display_in_project", "=", True),
                ],
            }
        )
        return action

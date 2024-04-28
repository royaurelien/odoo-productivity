import logging
import mimetypes
from base64 import b64decode
from io import BytesIO

import openpyxl

from odoo import _, fields, models
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
        string="Request for Quotation or Order",
        required=True,
        help="Upload a Request for Quotation or an Order file. Supported "
        "formats: XML and PDF (PDF with an embeded XML file).",
    )
    import_filename = fields.Char(
        string="Filename",
    )

    project_id = fields.Many2one(
        comodel_name="project.project",
        required=True,
    )

    def _get_supported_types(self):
        # Define the supported types dictionary
        supported_types = {
            "xlsx": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "xls": ("application/vnd.ms-excel"),
        }
        return supported_types

    def _parse_file(self, filename, filecontent, detect_doc_type=False):
        assert filename, "Missing filename"
        assert filecontent, "Missing file content"
        filetype = mimetypes.guess_type(filename)
        _logger.debug("Order file mimetype: %s", filetype)
        mimetype = filetype[0]
        supported_types = self._get_supported_types()

        _logger.error(type(filecontent))

        workbook = openpyxl.load_workbook(BytesIO(filecontent), read_only=True)

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
        else:
            raise UserError(
                _(
                    "This Import Type is not supported. Did you install "
                    "the module to support this type?"
                )
            )

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

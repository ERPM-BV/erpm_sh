# -*- coding: utf-8 -*-

from odoo import fields, models

class update_password_tag(models.TransientModel):
    _name = "update.password.tag"
    _inherit = "password.key.mass.update"
    _description = "Update password tags"

    tags_to_add_ids = fields.Many2many(
        "password.tag",
        "password_tag_update_password_tag_add_rel_table",
        "password_tag_id",
        "update_password_tag_id",
        string="Add tags",
    )
    tags_to_exclude_ids = fields.Many2many(
        "password.tag",
        "password_tag_update_password_tag_exclude_rel_table",
        "password_tag_id",
        "update_password_tag_id",
        string="Remove tags",
    )

    def _update_passwords(self, passwords_ids):
        """
        The method to prepare new vals for tags

        Args:
         * passwords_ids - password.key recordset

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        if self.tags_to_add_ids:
            to_add = []
            for tag in self.tags_to_add_ids.ids:
                to_add.append((4, tag))
            passwords_ids.write({"tag_ids": to_add,})
        if self.tags_to_exclude_ids:
            to_exclude = []
            for tag in self.tags_to_exclude_ids.ids:
                to_exclude.append((3, tag))
            passwords_ids.write({"tag_ids": to_exclude,})

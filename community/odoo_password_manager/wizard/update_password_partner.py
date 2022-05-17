# -*- coding: utf-8 -*-

from odoo import fields, models

class update_password_partner(models.TransientModel):
    _name = "update.password.partner"
    _inherit = "password.key.mass.update"
    _description = "Update Partner"

    partner_id = fields.Many2one(
        "res.partner",
        string="New Partner",
        required=False,
    )

    def _update_passwords(self, passwords_ids):
        """
        The method to prepare new vals for partner

        Args:
         * passwords_ids - password.key recordset

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        passwords_ids.write({"partner_id": self.partner_id.id})

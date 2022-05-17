# -*- coding: utf-8 -*-

from odoo import api, fields, models


class password_key_mass_update(models.TransientModel):
    """
    The wizard to be inherited in any update wizard which assume writing mass values in passwords
    """
    _name = "password.key.mass.update"
    _description = "Password Update"

    passwords = fields.Char(string="Updated passwords",)

    @api.model
    def create(self, values):
        """
        Overwrite to trigger passwords update

        Methods:
         * action_update_passwords

        Extra info:
         *  we do not use standard wizard buttons in the footer to use standard js forms
        """
        res = super(password_key_mass_update, self).create(values)
        res.action_update_passwords()
        return res

    def action_update_passwords(self):
        """
        The method to update passwords in batch

        Methods:
         * _update_passwords

        Extra info:
         * we use passwords char instead of m2m as ugly hack to avoid default m2m strange behaviour
         * Expected singleton
        """
        self.ensure_one()
        passwords_ids = self.passwords.split(",")
        passwords_ids = [int(pr) for pr in passwords_ids]
        passwords_ids = self.env["password.key"].browse(passwords_ids)
        if passwords_ids:
            self._update_passwords(passwords_ids)

    def _update_passwords(self, passwords_ids):
        """
        Dummy method to prepare values
        It is to be inherited in a real update wizard

        Args:
         * passwords_ids - password.key recordset
        """
        pass

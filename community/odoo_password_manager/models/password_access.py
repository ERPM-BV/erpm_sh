# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class password_access(models.Model):
    """
    The model to manage access to passwords and vaults
    """
    _name = "password.access"
    _description = "Password User Access"

    @api.constrains("access_level", "responsible_for_update")
    def _constrains_access_level_responsible_for_update(self):
        """
        The constrains for access_level responsible_for_update
        The goals are:
         * to make sure responsible for update has write rights for passwords
         * to make sure there is a single responsible
        """
        for access in self:
            if access.responsible_for_update and access.access_level not in ["admin", "full"]:
                raise UserError(_("Responsible for update should be either Admininstrator or should have full rights"))
            if len(access.bundle_id.access_ids.filtered(lambda acc: acc.responsible_for_update)) > 1:
                raise UserError(_("The might be only a single responsible assigned!"))

    @api.onchange("group_id")
    def _onchange_group_id(self):
        """
        Onchange method for group_id
        The goal is to make sure responsibles are only users, not groups and that groups and user are not assigned
        simultaneously
        """
        for access in self:
            if access.group_id:
                access.responsible_for_update = False
                access.user_id = False

    @api.onchange("user_id")
    def _onchange_user_id(self):
        """
        Onchange method for user_id
        The goal is to make sure that that groups and user are not assigned simultaneously
        """
        for access in self:
            if access.user_id:
                access.group_id = False

    @api.onchange("responsible_for_update")
    def _onchange_responsible_for_update(self):
        """
        Onchange method for responsible_for_update
        The goal is to make sure group is not assigned as responsible
        """
        for access in self:
            if access.responsible_for_update:
                access.group_id = False

    user_id = fields.Many2one(
        "res.users",
        string="User",
    )
    group_id = fields.Many2one(
        "res.groups",
        string="User group",
    )
    access_level = fields.Selection(
        [
            ("admin", "Admininstrator"),
            ("full", "Full rights"),
            ("readonly", "Readonly access"),
        ],
        string="Access Level",
        default="readonly",
    )
    bundle_id = fields.Many2one(
        "password.bundle",
        string="Bundle",
        ondelete="cascade",
    )
    responsible_for_update = fields.Boolean(
        string="Responsible for passwords update",
        help="For such a user activities to update passwords will be generated according to the bundle update policies"
    )

    _order = "access_level, id"

    @api.model
    def _return_all_bundles(self, cuser, modes=["admin"]):
        """
        The method to find all bundles this user has an access to
        Access level is defined per arg 'mode'

        Args:
         * cuser - self.env.user
         * modes - list of accesses ("admin", "full", "readonly")

        Methods:
         * _check_this_user

        Returns:
         * password.bundle recordset

        Extra info:
         * clear_caches is required to clean current bundles from cashe: in case of deletion it becomes a broken
           recordset
        """
        self.clear_caches()
        all_accesses = self.search([])
        res_accesses = all_accesses.filtered(
            lambda acc: acc.access_level in modes \
                        and (cuser.id == acc.user_id.id or acc.group_id.id in cuser.groups_id.ids)
        )
        bundles = res_accesses.mapped("bundle_id")
        return bundles

    @api.model
    def check_passwords_update(self):
        """
        Check wether passwords need update and create activities for responsible users if requried
        """
        self = self.sudo()
        responsible_access_ids = self.search([
            ("responsible_for_update", "=", True),
            ("user_id", "!=", False),
        ])
        for access in responsible_access_ids:
            self = self.with_user(user=access.user_id)
            access = access.with_user(user=access.user_id)
            delay = access.bundle_id.update_policy
            if delay > 0:
                last_update_date = fields.Date.today() - timedelta(days=delay)
                passwords = self.env["password.key"].search([
                    ("bundle_id", "=", access.bundle_id.id),
                    ("no_update_required", "=", False),
                    ("mail_activity_update_id", "=", False),
                    "|",
                        ("password_update_date", "=", False),
                        ("password_update_date", "<=", last_update_date),
                ])
                for password in passwords:
                    values = {
                        "res_id": password.id,
                        "res_model_id": self.env["ir.model"]._get_id(name="password.key"),
                        "activity_type_id": self.sudo().env.ref("odoo_password_manager.mail_activity_data_update_password").id,
                        "summary": _("Update password"),
                        "date_deadline": fields.date.today(),
                        "user_id": access.user_id.id,
                    }
                    activity = self.env["mail.activity"].create(values)
                    password.mail_activity_update_id = activity

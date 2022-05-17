# -*- coding: utf-8 -*-

from odoo import fields, models


class bundle_login(models.TransientModel):
    """
    The wizard to enter password for this bumd;e
    """
    _name = "bundle.login"
    _description = "Passwords Bundle Log In"

    bundle_id = fields.Many2one(
        "password.bundle",
        string="Passwords Bundle",
        required=False,
    )
    password = fields.Char(
        string="Password",
        required=True,
    )

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class password_generator(models.TransientModel):
    """
    The wizard to generate a new password based on requirements
    """
    _name = "password.generator"
    _description = "Password Generator"

    def return_charset(self):
        """
        The method to return possible charsets
        """
        return [
            ("ascii_62", "All digits and upper & lowercase letters"),
            ("ascii_50", "All digits and upper & lowercase letters (exclude visually similar characters)"),
            ("ascii_72", "All digits, upper & lowercase letters and special symbols"),
            ("hex", "Lower case hexadecimal"),
        ]

    @api.model
    def default_pwlength(self):
        """
        Default method for length
        """
        ICPSudo = self.env['ir.config_parameter'].sudo()
        return int(ICPSudo.get_param('defau_password_length', default='10'))

    @api.model
    def default_pwcharset(self):
        """
        Default method for charset
        """
        ICPSudo = self.env['ir.config_parameter'].sudo()
        return ICPSudo.get_param('defau_password_charset', default='ascii_62')

    pwlength = fields.Integer(
        string="Length",
        default=default_pwlength,
    )
    pwcharset = fields.Selection(
        return_charset,
        string="Complexity",
        default=default_pwcharset,
    )

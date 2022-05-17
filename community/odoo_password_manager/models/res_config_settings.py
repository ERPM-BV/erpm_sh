# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval

PARAMS = [
    ("password_management_export_option", safe_eval, "False"),
    ("generate_passord_on_create", safe_eval, "False"),
    ("defau_password_length", int, "10"),
    ("defau_password_charset", str, "ascii_62"),
]


class res_config_settings(models.TransientModel):
    """
    Overwrite to add own settings
    """
    _inherit = "res.config.settings"

    def return_charset(self):
        """
        The method to return possible charsets
        """
        return self.env["password.generator"].return_charset()

    password_management_export_option = fields.Boolean(string="Export passwords")
    passwords_ir_actions_server_ids = fields.Many2many(
        "ir.actions.server",
        "ir_actions_server_res_config_setting_rel_table",
        "ir_actions_server_id",
        "res_config_setting_id",
        string="Mass actions for passwords",
        domain=[("model_id.model", "=", "password.key")],
    )
    generate_passord_on_create = fields.Boolean(string="Generate passwords on create")
    defau_password_length = fields.Integer(string="Default length for generated password")
    defau_password_charset = fields.Selection(
        return_charset,
        string="Default requirements for password",
    )
    module_odoo_password_manager_custom_fields = fields.Boolean(string="Custom fields for passwords")

    @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        res = super(res_config_settings, self).get_values()
        values = {}
        for field_name, getter, default in PARAMS:
            values[field_name] = getter(str(Config.get_param(field_name, default)))
        passwords_ir_actions_server_ids =  safe_eval(
            Config.get_param("odoo_password_manager.passwords_ir_actions_server_ids", "[]")
        )
        existing_ids = self.env["ir.actions.server"].search([("id", "in", passwords_ir_actions_server_ids)]).ids
        values.update({"passwords_ir_actions_server_ids": [(6, 0, existing_ids)]})
        res.update(**values)
        return res

    def set_values(self):
        """
        Overwrite to add new system params

        To-do:
         * pass decryption key to hooks
         * the method update decryption key (all password would be decrypted and ecrypted back). The problem is that
           no user have an access to all keys. It is better to do that not in hooks but per password bundle and keep
           the key there per each bundle
         * apply to decryption key should require security password
         * for some reasons spaces are removed
        """
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, getter, default in PARAMS:
            value = getattr(self, field_name, default)
            Config.set_param(field_name, value)
        Config.set_param(
            "odoo_password_manager.passwords_ir_actions_server_ids", self.passwords_ir_actions_server_ids.ids
        )

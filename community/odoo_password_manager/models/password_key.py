# -*- coding: utf-8 -*-

import base64
import logging
from werkzeug import urls


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, AccessError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    # for the version from 1.7
    import passlib.pwd as pwd
    def pw_generate(length, charset):
        return pwd.genword(length=length, charset=charset)
except:
    # for the version after 1.7
    import passlib.utils as pwd
    def pw_generate(length, charset):
        return pwd.generate_password(size=length, charset=charset)

try:
    from zxcvbn import zxcvbn
except ImportError as e:
    _logger.error(e)
    def zxcvbn(password):
        return 0

ALLOWED_UNDER_SUDO = ["odoo_password_manager.password_key_add_to_favourite", 
                      "odoo_password_manager.password_key_remove_from_favourite"]

class password_key(models.Model):
    """
    The model to keep passwords and related info
    """
    _name = "password.key"
    _inherit = ["mail.activity.mixin", "mail.thread"]
    _description = "Password"

    @api.model
    def default_bundle_id(self):
        """
        Default method for bundle_id (needed in case of page refresh)
        """
        if self.env.context.get("params") and self.env.context.get("params").get("default_bundle_id"):
            return self.env.context.get("params").get("default_bundle_id")

    def _inverse_link_url(self):
        """
        Inverse method for link_url
        The goal is to make an url have proper format

        Methods:
         * url_parse of werkzeugurls
        """
        for password in self:
            clean_url = password.link_url
            if clean_url:
                url = urls.url_parse(clean_url)
                if not url.scheme:
                    if not url.netloc:
                        url = url.replace(netloc=url.path, path='')
                    clean_url = url.replace(scheme='http').to_url()
            if clean_url != password.link_url:
                password.link_url = clean_url

    def _inverse_attachment_ids(self):
        """
        Inverse method for attachment_ids
        The goal is to make attachments ordinary one with stated res_id
        """
        for password in self:
            password.attachment_ids.write({"res_id": password.id})

    @api.onchange("password")
    def _onchange_password(self):
        """
        Onchange method for password
        The goal is to show calculated strength in real time
        """
        for passwordkey in self:
            passwordkey.password_streng = passwordkey.password and str(zxcvbn(passwordkey.password).get("score")) or "0"

    @api.model
    def _generate_order_by(self, order_spec, query):
        """
        Specify how to proceed the technical search by name - to lower case it
        """
        res = super(password_key, self)._generate_order_by(order_spec=order_spec, query=query)
        if "name asc" or "name desc" in order_spec:
            res = res.replace('"password_key"."value"', 'LOWER("password_key"."value")')
            res = res.replace('"password_key"."name"', 'LOWER("password_key"."name")')
        return res

    name = fields.Char(string="Reference")
    bundle_id = fields.Many2one(
        "password.bundle",
        string="Bundle",
        ondelete="cascade",
        default=default_bundle_id,
    )
    user_name = fields.Char(string="User name")
    password = fields.Char(string="Password",)
    password_streng = fields.Selection(
        [
            ('0', _('Horrible')),
            ('1', _('Bad')),
            ('2', _('Weak')),
            ('3', _('Good')),
            ('4', _('Strong')),
        ],
        string="Password Strength",
    )
    confirm_password = fields.Char(string="Confirm Password",)
    password_update_date = fields.Date(
        string="Password is updated on",
        readonly=True,
    )
    mail_activity_update_id = fields.Many2one(
        "mail.activity",
        string="Mail Activity to update password",
    )
    email = fields.Char(string="Email")
    link_url = fields.Char(
        string="URL",
        inverse=_inverse_link_url,
    )
    phone = fields.Char(string="Phone",)
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
    )
    tag_ids = fields.Many2many(
        "password.tag",
        "password_tag_password_key_rel_table",
        "password_tag_id",
        "password_key_id",
        string="Tags",
    )
    notes = fields.Html(string="Notes")
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'ir_attachment_password_key_rel_table',
        'attachment_id',
        'password_key_id',
        string='Attachments',
        copy=True,
        inverse=_inverse_attachment_ids,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    favourite_user_ids = fields.Many2many(
        "res.users",
        "res_users_password_key_rel_favor_table",
        "res_users_favor_id",
        "password_key_favor_id",
        string="Favourite of",
        copy=False,
    )
    no_update_required = fields.Boolean(
        string="No Update Required",
        help="If checked, bundle update policies will not generate activities for this password",
    )

    _order = "name ASC, id"

    def read(self, fields=None, load='_classic_read'):
        """
        Overwrite to decrypt passwords while reading

        Methods:
         * check_action_security - although it is an excess check from interface purpose, it is done to avoid
                                   manipulations with js and xmk
        """
        result = super(password_key, self).read(fields=fields, load=load)
        for passwordkey_dict in result:
            if passwordkey_dict.get("password") or passwordkey_dict.get("confirm_password"):
                bundle_id = self.browse(passwordkey_dict.get("id")).bundle_id
                cant_decrypt = self.env["password.bundle"].check_action_security(
                    res_model="password.key",
                    res_ids=[passwordkey_dict.get("id")],
                    viewtype="form"
                )
                if cant_decrypt:
                    raise AccessError(
                        _(u"Access Denied! Please login from the bundle {}".format(bundle_id and bundle_id.name or ""))
                    )
                if passwordkey_dict.get("password"):
                    passwordkey_dict.update({
                        "password": bundle_id.decrypt_key(passwordkey_dict.get("password"))
                    })
                if passwordkey_dict.get("confirm_password"):
                    passwordkey_dict.update({
                        "confirm_password": bundle_id.decrypt_key(passwordkey_dict.get("confirm_password"))
                    })
        return result

    @api.model
    def create(self, values):
        """
        Overwrite to decrypt password and confirm_password

        Methods:
         * encrypt_key
        """
        if not self._context.get("no_more_check"):
            if self.env.context.get("import_file") and not values.get("confirm_password"):
                values["confirm_password"] = values.get("password")
            if values.get("password") != values.get("confirm_password"):
                raise ValidationError(_("Password and its confirmation are not equal!"))
        bundle_to_edit = values.get("bundle_id") or self.env.context.get("default_bundle_id") \
                         or (
                                self.env.context.get("params")
                                and self.env.context.get("params").get("default_bundle_id")
                            ) \
                         or False
        bundle_id = self.env["password.bundle"].browse(bundle_to_edit)
        values["password_streng"] = values.get("password") and str(zxcvbn(values.get("password")).get("score")) or "0"
        values["password"] = bundle_id.encrypt_key(values.get("password"))
        values["confirm_password"] = bundle_id.encrypt_key(values.get("confirm_password"))
        values["password_update_date"] = fields.Date.today()
        res = super(password_key, self).create(values)
        return res

    def write(self, values):
        """
        Overwrite to decrypt password and confirm_password
        In case bundle id or password or confirm password are changed --> encrypt password

        Methods:
         * encrypt_key
        """
        if not self._context.get("no_more_check"):
            if values.get("password") != values.get("confirm_password"):
                raise ValidationError(_("Password and its confirmation are not equal!"))
        res = True
        action_update_done = False
        for passwordkey in self:
            new_values = values.copy()
            if new_values.get("bundle_id") or new_values.get("password") or new_values.get("confirm_password"):
                bundle_id = self.env["password.bundle"].browse(new_values.get("bundle_id") or passwordkey.bundle_id.id)
                passwordkey_dict = passwordkey.read()[0]
                password = new_values.get("password") or passwordkey_dict.get("password")
                confirm_password = new_values.get("confirm_password") or passwordkey_dict.get("confirm_password")
                new_values["password"] = bundle_id.encrypt_key(password)
                new_values["confirm_password"] = bundle_id.encrypt_key(confirm_password)
                new_values["password_streng"] = password and str(zxcvbn(password).get("score")) or "0"
                if new_values.get("password"):
                    new_values["password_update_date"] = fields.Date.today()
                    action_update_done = True

            res = super(password_key, passwordkey).write(new_values)
            if action_update_done and passwordkey.mail_activity_update_id:
                # if password is update mail activity should be marked done
                passwordkey.mail_activity_update_id.action_done()
        return res

    def export_data(self, fields_to_export):
        """
        Re-write to decrypt passwords when exporting

        1. export data indexes of password and confirm password if any
        2. check that for all exported keys security is fine
        3. go by each expported password > convert according to the bunlde descryption
           IMPORTANT: here we assume that export_data order is absolutely the same as in self. 

        """
        result = super(password_key, self).export_data(fields_to_export=fields_to_export)
        # 1
        to_descrypt_indexes = []
        for e_index, e_field in enumerate(fields_to_export):
            if e_field in ["password", "confirm_password"]:
                to_descrypt_indexes.append(e_index)
        if to_descrypt_indexes:
            # 2
            cant_decrypt = self.env["password.bundle"].check_action_security(
                res_model="password.key",
                res_ids=self.ids,
                viewtype="form"
            )
            if cant_decrypt:
                raise AccessError(
                    _(u"Access Denied! Please login from the bundle {}".format(bundle_id and bundle_id.name or ""))
                )
            # 3
            l_datas = result.get("datas")
            result_index = 0
            for pw_key in self:
                bundle_id = pw_key.bundle_id
                for field_index in to_descrypt_indexes:
                    l_datas[result_index][field_index] = bundle_id.decrypt_key(l_datas[result_index][field_index])
                result_index += 1
            result.update({"datas": l_datas})
        return {"datas": l_datas}

    @api.model
    def default_get(self, fields):
        """
        Overwrite to pass password default value
        The reason fo not using just 'default', since we should have the same value for password and confirm_password

        Methods:
         * generate_password_passlib
        """
        values = super(password_key, self).default_get(fields)
        Config = self.env['ir.config_parameter'].sudo()
        need_default = safe_eval(Config.get_param("generate_passord_on_create", "False"))
        pw_default = False
        if need_default:
            length = int(Config.get_param('defau_password_length', default='10'))
            charset = Config.get_param('defau_password_charset', default='ascii_62')
            pw_default = self.generate_password_passlib(length, charset)
        values.update({
            "password": pw_default,
            "confirm_password": pw_default,
        })
        return values

    def return_selected_passwords(self):
        """
        The method to return selected passwords

        Methods:
         * _return_mass_actions

        Returns:
         * list of 2 lists & boolean & dict:
          ** dicts of passwords values requried for mass operations
          ** dicts of mass actions
          ** whether export is turned on
          ** dict of password values if there is only one in self or false
        """
        self = self.with_context(lang=self.env.user.lang)
        passwords = []
        for password in self:
            passwords.append({
                "id": password.id,
                "name": password.name_get()[0][1],
                "user_name": password.user_name,
                "link_url": password.link_url,
                "password": password.read()[0].get("password"),
            })
        single_password = False
        actions = self._return_mass_actions()
        Config = self.env['ir.config_parameter'].sudo()
        export_conf = safe_eval(Config.get_param("password_management_export_option", "False"))
        return [passwords, actions, export_conf, single_password]

    def rerurn_all_pages_ids(self, domain):
        """
        The method to search passwords by js domain

        Returns:
         *  list of all passwords articles
        """
        all_passwords = set(self.ids + self.search(domain).ids)
        return list(all_passwords)

    @api.model
    def _return_mass_actions(self):
        """
        The method to return available mass actions in js format

        Returns:
         * list of dict
           ** id
           ** name
        """
        Config = self.env['ir.config_parameter'].sudo()
        mass_actions = safe_eval(Config.get_param("odoo_password_manager.passwords_ir_actions_server_ids", "[]"))
        self = self.sudo().with_context(lang=self.env.user.lang)
        res = []
        for action in mass_actions:
            action_id = self.env["ir.actions.server"].browse(action)
            try:
                if action_id.id:
                    res.append({
                        "id": action,
                        "name": action_id.name,
                    })
            except:
                _logger.warning("The action {} has been deleted".format(action))
        return res

    def proceed_mass_action(self, action):
        """
        The method to trigger mass action for selected passwords

        Args:
         * action - ir.actions.server id

        Methods:
         * run() of ir.actions.server
        """
        context = self.env.context.copy()
        active_ids = self.ids
        context.update({
            "active_id": self.ids[0],
            "active_ids": self.ids,
            "active_model": "password.key"
        })
        for allow_sudo in ALLOWED_UNDER_SUDO:
            action_ch_id = self.sudo().env.ref(allow_sudo) and self.sudo().env.ref(allow_sudo).id or 0
            if action == action_ch_id:
                self = self.sudo()
                break
        res = self.env["ir.actions.server"].browse(action).with_context(context).run()
        if res:
            if res.get("view_id"):
                res = {
                    "view_id": res.get("view_id")[0], 
                    "res_model": res.get("res_model"), 
                    "display_name": res.get("display_name"),
                }
            elif res.get("type").find("ir.actions") != -1:
                res = {"action": res}
        return res

    @api.model
    def return_edit_form(self):
        """
        The method to return password key editing form
        """
        view_id = self.sudo().env.ref('odoo_password_manager.password_key_view_form').id
        return view_id

    @api.model
    def generate_password_passlib(self, length, charset):
        """
        The method to generate a new password

        Args:
         * length - int
         * charset - selection (observe password.generator model)

        Returns:
         * unicode
        """
        if not length or length <= 0 or not charset:
            raise ValidationError(_("Please select proper password length and complexity"))
        return pw_generate(length, charset)

    def mark_as_favourite(self):
        """
        The action to add the password to favourites
        """
        self.ensure_one()
        current_user = self.env.user.id
        if current_user in self.favourite_user_ids.ids:
            self.sudo().favourite_user_ids = [(3, current_user)]
        else:
            self.sudo().favourite_user_ids = [(4, current_user)]

# -*- coding: utf-8 -*-

import base64
import logging

import passlib.context

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, AccessError
from odoo.http import request
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
except ImportError as e:
    _logger.error(e)

CRYPT_CONTEXT = passlib.context.CryptContext(['pbkdf2_sha512'],)


class password_bundle(models.Model):
    """
    The model to manage passwords bundle (vaults)
    """
    _name = "password.bundle"
    _description = "Passwords Bundle"

    @api.model
    def _default_access_ids(self):
        """
        Default method for access_ids
        """
        values = {
            "user_id": self.env.user.id,
            "access_level": "admin",
        }
        return [(0, 0, values)]

    def _compute_has_read_right_to(self):
        """
        Compute method for has_read_right_to and has_full_right_to
        """
        current_user = self.env.user
        groups = current_user.groups_id
        self = self.sudo()
        r_bundles = self.env["password.access"]._return_all_bundles(current_user, modes=["readonly", "full", "admin"])
        w_bundles = self.env["password.access"]._return_all_bundles(current_user, modes=["full", "admin"])
        a_bundles = self.env["password.access"]._return_all_bundles(current_user, modes=["admin"])
        for bundle in self:
            bundle.has_read_right_to = bundle in r_bundles and [(6, 0, [current_user.id])] or False
            bundle.has_full_right_to = bundle in w_bundles and [(6, 0, [current_user.id])] or False
            bundle.has_admin_right_to = bundle in a_bundles and [(6, 0, [current_user.id])] or False

    @api.model
    def search_has_read_right_to(self, operator, value):
        """
        Search method for has_read_right_to

        Methods:
         * _return_all_bundles of password.access

        Returns:
         * RPN domain
        """
        current_user = self.env["res.users"].browse(value)
        groups = current_user.groups_id
        self = self.sudo()
        bundles = self.env["password.access"]._return_all_bundles(current_user, modes=["readonly", "full", "admin"])
        return [('id', 'in', bundles.ids)]

    @api.model
    def search_has_full_right_to(self, operator, value):
        """
        Search method for has_full_right_to

        Methods:
         * _return_all_bundles of password.access

        Returns:
         * RPN domain
        """
        current_user = self.env.user.browse(value)
        groups = current_user.groups_id
        self = self.sudo()
        bundles = self.env["password.access"]._return_all_bundles(current_user, modes=["full", "admin"])
        return [('id', 'in', bundles.ids)]

    @api.model
    def search_has_admin_right_to(self, operator, value):
        """
        Search method for search_has_admin_right_to

        Methods:
         * _return_all_bundles of password.access

        Returns:
         * RPN domain
        """
        current_user = self.env.user.browse(value)
        groups = current_user.groups_id
        self = self.sudo()
        bundles = self.env["password.access"]._return_all_bundles(current_user, modes=["admin"])
        return [('id', 'in', bundles.ids)]

    def _inverse_password(self):
        """
        Inverse method for extra_password_security, password and confirm_password

        Methods:
         * _update_session_bundles
        """
        for bundle in self:
            if bundle.extra_password_security and bundle.password:
                bundle.password_update_time = fields.Datetime.now()
                bundle._update_session_bundles()

    def _inverse_active(self):
        """
        Inverse method for active
        """
        for bundle in self:
            if not bundle.active:
                passwords = self.env["password.key"].search([("bundle_id", "=", bundle.id)])
                passwords.write({"active": False})

    @api.constrains('extra_password_security', 'session_length')
    def _check_extra_password_security(self):
        """
        Constraint to make session length long enough
        """
        for bundle in self:
            if bundle.extra_password_security and bundle.session_length < 3:
                raise ValidationError(_(
                    "Session should be at least 3 minutes. Otherwise users will be not able to find a password"
                ))

    name = fields.Char(string="Name")
    notes = fields.Html(string="Notes")
    update_policy = fields.Integer(
        string="Update passwords each (days)",
        help="""
            If set more than 0, Odoo will automatically generate activities to update definite passwords per each
            period in specified days
        """,
    )
    passwords_ids = fields.One2many(
        "password.key",
        "bundle_id",
        string="Passwords",
    )
    tag_ids = fields.One2many(
        "password.tag",
        "bundle_id",
        string="Available tags",
    )
    access_ids = fields.One2many(
        "password.access",
        "bundle_id",
        string="Access Levels",
        copy=True,
        help="""
            === Bundles ===
            A user may access (read) passwords' bundle:
             * if this user is its creator
             * if this user has any access level

            A user may create, update (including change of extra bundle password) or delete passwords' bundle:
             * if this user is its creator
             * this user has the 'Administrator' access level

            === Passwords ===
            A user may access (read) a password:
             * if this user is a related bundle creator
             * if this user has any access level to a related bundle

            A user may may create, update or delete a password:
             * if this user is a related bundle creator
             * if this user has the 'Full rights' access level to a related bundle

            === Tags ===
            A user may access password tags:
             * if this user is a related bundle creator
             * if this user has any access level to a related bundle

            A user may create, update or delete password tags:
             * if this user is a related bundle creator
             * if this user has the 'Full rights' access level to a related bundle
        """,
        default=_default_access_ids,
    )
    color = fields.Integer(string="Color Index")
    active = fields.Boolean(
        string="Active",
        default=True,
        inverse=_inverse_active,
    )
    has_read_right_to = fields.Many2many(
        "res.users",
        "res_users_password_bundle_rel_table_readonly",
        "res_users_id",
        "password_bundle_id",
        string="Current user has read rights to this bundle",
        compute=_compute_has_read_right_to,
        search='search_has_read_right_to',
    )
    has_full_right_to = fields.Many2many(
        "res.users",
        "res_users_password_bundle_rel_table_full",
        "res_users_id",
        "password_bundle_id",
        string="Current user has write rights to this bundle",
        compute=_compute_has_read_right_to,
        search='search_has_full_right_to',
    )
    has_admin_right_to = fields.Many2many(
        "res.users",
        "res_users_password_bundle_rel_table_admin",
        "res_users_id",
        "password_bundle_id",
        string="Current user has full right to this bundle",
        compute=_compute_has_read_right_to,
        search='search_has_admin_right_to',
    )
    extra_password_security = fields.Boolean(
        string="Extra password to open this bundle",
        help="""
            If turned on, users will have to enter a paraphrase before accessing passwords or changing this bundle.
            BE CAUTIOUS: if you forgot the paraphrase you would LOOOSE password data. Paraphrase is hashed and
            can't be recovered by any user disregarding his/her access rights
        """,
    )
    password = fields.Char(
        string="Bundle Password",
        inverse=_inverse_password,
        copy=False,
    )
    password_update_time = fields.Datetime(
        string="Password update time",
        readonly=True,
        default=lambda self: fields.Datetime.now(),
    )
    confirm_password = fields.Char(
        string="Confirm Bundle Password",
        inverse=_inverse_password,
        copy=False,
    )
    session_length = fields.Integer(
        string="Max Session Length (Minutes)",
        default=60,
    )
    bundle_key = fields.Text(
        string="Key",
        readonly=True,
    )

    def init(self):
        """
        Re-write to encrypt passwords (the method is copied from res.users)
         allow setting plaintext passwords via SQL and have them automatically encrypted at startup: look for passwords
         which don't match the "extended" MCF and pass those through passlib.
         Alternative: iterate on *all* passwords and use CryptContext.identify
        """
        cr = self.env.cr
        cr.execute("""
        SELECT id, password FROM password_bundle
        WHERE password IS NOT NULL
          AND password !~ '^\$[^$]+\$[^$]+\$.'
        """)
        if self.env.cr.rowcount:
            bundles = self.sudo()
            for uid, pw in cr.fetchall():
                bundles.browse(uid).write({"password": pw, "confirm_password": pw})

    @api.model
    def create(self, values):
        """
        Overwrite to generate new key

        Methods:
         * action_update_bundle_key
        """
        pw_values = self._set_encrypted_password(values, values.get("extra_password_security"))
        if pw_values:
            values.update(pw_values)
        res = super(password_bundle, self).create(values)
        res.action_update_bundle_key()
        return res

    def write(self, values):
        """
        Overwrite to decrypt password if any

        Extra info:
         * we make update of 
        """  
        for bundle in self:
            bundle_old_security = bundle.extra_password_security
            if values.get("extra_password_security") is not None:
                bundle_old_security = values.get("extra_password_security")
            pw_values = self._set_encrypted_password(values, bundle_old_security)
            if pw_values:
                values.update(pw_values)
            res = super(password_bundle, bundle).write(values)
        return res

    def action_open_bundle_passwords(self):
        """
        The method to open passwords of this bundle
        """
        action_id = self.sudo().env.ref("odoo_password_manager.password_key_action").read()[0]
        ctx = safe_eval(action_id.get("context"))
        ctx.update({"default_bundle_id": self.ids[0]})
        action_id["context"] = ctx.copy()
        action_id["display_name"] = self.name
        action_id["domain"] = [("bundle_id", "in", self.ids)]
        return action_id

    @api.model
    def _set_encrypted_password(self, values, extra_password_security):
        """
        The method to encrypt password
         1. depending on the lib version
         2. clear passwords if extra security is not needed (to avoid their further double decryption)
    
        Args:
         * values - to create / to write values
         * extra_password_security - boole whether password should be checked   
        
        Returns:
         * dict of values
        """
        res_values = {}
        if  values.get("password") is not None or values.get("confirm_password") is not None \
                or values.get("extra_password_security") is not None:
            if extra_password_security:
                if values.get("password") != values.get("confirm_password"):
                    raise ValidationError(_("Password and its confirmation are not equal!"))
                try:
                    bpw = CRYPT_CONTEXT.hash(values.get("password"))
                except:
                    try:
                        bpw = CRYPT_CONTEXT.encrypt(values.get("password"))
                    except:
                        raise ValidationError(_("Something goes wrong. Please try to refresh the page"))
                assert CRYPT_CONTEXT.identify(bpw) != 'plaintext'
                if bpw == values.get("password"):
                    raise ValidationError(_("Something goes wrong. Please try to refresh the page"))
                res_values = {"password": bpw, "confirm_password": bpw}
            else:
                # 2
                res_values = {"password": False, "confirm_password": False}                
        return res_values

    @api.model
    def check_action_security(self, res_model, res_ids=[], viewtype="kanban"):
        """
        The method to check whether this user
         1. Bundles kanban and list should not be checked since the list should be shown
         2. When no session last login > user must enter password
         3. If last login is before password update > user must enter password
         4. Otherwise consider how much time left from the previous login

        Args:
         * res_model - char
         * res_ids - list of ids to check
         * viewtype - char - current action view type

        Returns:
         * id - int - bundle which requires login ???

        Extra info:
         * basically, here we should work with a single bundle, since there might only a single password. In case of
           bundles list security is not required
         * session_bundles format: {1: datetime.datetime}
        """
        if not res_ids:
            return False
        if res_model == "password.bundle":
            if viewtype != "form":
                # 1
                return False
            else:
                bundles_to_check = self.browse(res_ids)
        else:
            bundles_to_check = self.env[res_model].browse(res_ids).mapped("bundle_id")
        xml_id = self.sudo().env.ref("odoo_password_manager.bundle_login_wizard_form_view").id
        for bundle in bundles_to_check:
            if bundle.extra_password_security:
                session_bundles = request.session.get("pw_bundles")
                if session_bundles:
                    this_bundle_last_login = session_bundles.get(bundle.id)
                    if not this_bundle_last_login:
                        # 2
                        return [bundle.id, xml_id, bundle.name]
                    else:
                        last_login = fields.Datetime.from_string(this_bundle_last_login)
                        if bundle.password_update_time and last_login < bundle.password_update_time:
                            # 3
                            return [bundle.id, xml_id, bundle.name]
                        else:
                            # 4
                            now = fields.Datetime.now()
                            diff = (now - last_login).total_seconds() / 60
                            if bundle.session_length < diff:
                                return [bundle.id, xml_id, bundle.name]
                else:
                    return [bundle.id, xml_id, bundle.name]
        return False

    def action_login_bundle(self, password):
        """
        The method to login and update session

        Args:
         * password - char - password to check

        Methods:
         * _update_session_bundles

        Returns:
         * bool: true if verification is succesfull, false - otherwise

        Extra info:
         * Expected singleton
         * session_bundles format: {1: datetime.datetime}
        """
        if not password:
            raise AccessError(_("The entered password is not correct"))
        self.ensure_one()
        self.env.cr.execute(
            "SELECT COALESCE(password, '') FROM password_bundle WHERE id=%s",
            [self.id]
        )
        [hashed] = self.env.cr.fetchone()
        valid = CRYPT_CONTEXT.verify(password, hashed)
        if valid:
            self._update_session_bundles()
        else:
            raise AccessError(_("The entered password is not correct"))
        return valid

    def _update_session_bundles(self):
        """
        The method to add current bundle to session
        """
        for bundle in self:
            session_bundles = request.session.get("pw_bundles") or {}
            session_bundles.update({bundle.id: fields.Datetime.now()})
            request.session["pw_bundles"] = session_bundles

    @api.model
    def return_bundles_action(self):
        """
        The method to return standard bundles action

        Returns:
         * dict of ir.actions.window
        """
        return self.sudo().env.ref("odoo_password_manager.password_bundle_action").read()[0]

    @api.model
    def return_all_active_bundles(self):
        """
        The method to retrieve all bundles of active user for 'all passwords'

        Returns:
         * list
        """
        return self.search([]).ids

    def action_update_bundle_key(self):
        """
        The method to generate a new key to encrypt / decrypt passwods
         1. In case there are passwords they should be decrypted with old key and encrypted with a new one

        To-do:
         * think whether saving as binary migth make problems

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        try:
            old_key = self.bundle_key
            self.bundle_key = Fernet.generate_key()
            password_ids = self.env["password.key"].search([
                ("bundle_id", "=", self.id),
                "|",
                    ("active", "=", True),
                    ("active", "=", False),
            ])
            password_ids.with_context(old_bundle_key=old_key).write({"bundle_id": self.id})
        except:
            _logger.warning("Encryption key can't be updated")

    def encrypt_key(self, password):
        """
        The method to encrypt password usign the bundle_key

        Args:
         * password - char

        Returns:
         * char
        """
        encrypted_key = password
        if password:
            if self and self.bundle_key:
                try:
                    fe = Fernet(self.bundle_key)
                    password = password.encode()
                    encrypted_key = fe.encrypt(password)
                    encrypted_key = encrypted_key.decode()
                except:
                    _logger.warning("Password can't be encrypted")
            else:
                _logger.warning("Password can't be encrypted since related bundle doesn't have a key")
        return encrypted_key

    def decrypt_key(self, password):
        """
        The method to encrypt password usign the bundle_key

        Args:
         * password - char

        Returns:
         * char
        """
        if self.env.context.get("old_bundle_key") is not None:
            bundle_key = self.env.context.get("old_bundle_key")
        else:
            bundle_key = self.bundle_key
        decrypted_key = password
        if password:
            if self and bundle_key:
                try:
                    fe = Fernet(bundle_key)
                    password = password.encode()
                    password = fe.decrypt(password)
                    decrypted_key = password.decode()
                except Exception as error:
                    _logger.warning("Password can't be decrypted: {}".format(error))
            else:
                _logger.warning("Password can't be decrypted since related bundle doesn't have a key")
        return decrypted_key

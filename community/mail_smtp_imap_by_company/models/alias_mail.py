# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import ast
import base64
import datetime
import dateutil
import email
import email.policy
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
import threading

from collections import namedtuple
from email.message import EmailMessage
from lxml import etree
from werkzeug import urls
from xmlrpc import client as xmlrpclib

from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID
from odoo.exceptions import MissingError
from odoo.osv import expression
from odoo.tools import remove_accents

from odoo.tools import ustr
from odoo.tools.misc import clean_context, split_every

_logger = logging.getLogger(__name__)

class AliasMixinInherit(models.AbstractModel):
    _inherit = 'mail.alias.mixin'
    
    def _alias_filter_fields(self, values, filters=False):
        """ Split the vals dict into two dictionnary of vals, one for alias
        field and the other for other fields """
        if not filters:
            filters = self.env['mail.alias']._fields.keys()
        alias_values, record_values = {}, {}
        for fname in values.keys():
            if fname in filters and not 'name' in filters:
                alias_values[fname] = values.get(fname)
            else:
                record_values[fname] = values.get(fname)
        return alias_values, record_values

class MailThreadInherit(models.AbstractModel):
    
    _inherit = 'mail.thread'
    
    @api.model
    def message_route(self, message, message_dict, model=None, thread_id=None, custom_values=None):

        if not isinstance(message, EmailMessage):
            raise TypeError('message must be an email.message.EmailMessage at this point')
        catchall_alias = self.env['ir.config_parameter'].sudo().get_param("mail.catchall.alias")
        bounce_alias = self.env['ir.config_parameter'].sudo().get_param("mail.bounce.alias")
        fallback_model = model

        # get email.message.Message variables for future processing
        message_id = message_dict['message_id']

        # compute references to find if message is a reply to an existing thread
        thread_references = message_dict['references'] or message_dict['in_reply_to']
        msg_references = [ref for ref in tools.mail_header_msgid_re.findall(thread_references) if 'reply_to' not in ref]

        mail_messages = self.env['mail.message'].sudo().search([('message_id', 'in', msg_references)], limit=1, order='id desc, message_id')
        is_a_reply = bool(mail_messages)
        reply_model, reply_thread_id = mail_messages.model, mail_messages.res_id

        # author and recipients
        email_from = message_dict['email_from']
        email_from_localpart = (tools.email_split(email_from) or [''])[0].split('@', 1)[0].lower()
        email_to = message_dict['to']
        email_to_localparts = [
            e.split('@', 1)[0].lower()
            for e in (tools.email_split(email_to) or [''])
        ]
        # Delivered-To is a safe bet in most modern MTAs, but we have to fallback on To + Cc values
        # for all the odd MTAs out there, as there is no standard header for the envelope's `rcpt_to` value.
        rcpt_tos_localparts = [
            e.split('@')[0].lower()
            for e in tools.email_split(message_dict['recipients'])
        ]
        rcpt_tos_valid_localparts = [to for to in rcpt_tos_localparts]

        #geminatecs
        email_to_alias_domain_list = [
            e.split('@')[1].lower()
            for e in tools.email_split(message_dict['recipients'])
        ]
        #geminatecs


        # 0. Handle bounce: verify whether this is a bounced email and use it to collect bounce data and update notifications for customers
        #    Bounce alias: if any To contains bounce_alias@domain
        #    Bounce message (not alias)
        #       See http://datatracker.ietf.org/doc/rfc3462/?include_text=1
        #        As all MTA does not respect this RFC (googlemail is one of them),
        #       we also need to verify if the message come from "mailer-daemon"
        #    If not a bounce: reset bounce information
        if bounce_alias and any(email == bounce_alias for email in email_to_localparts):
            self._routing_handle_bounce(message, message_dict)
            return []
        if message.get_content_type() == 'multipart/report' or email_from_localpart == 'mailer-daemon':
            self._routing_handle_bounce(message, message_dict)
            return []
        self._routing_reset_bounce(message, message_dict)

        # 1. Handle reply
        #    if destination = alias with different model -> consider it is a forward and not a reply
        #    if destination = alias with same model -> check contact settings as they still apply
        if reply_model and reply_thread_id:
            reply_model_id = self.env['ir.model']._get_id(reply_model)
            other_model_aliases = self.env['mail.alias'].search([
                '&', '&',
                ('alias_name', '!=', False),
                ('alias_name', 'in', email_to_localparts),
                ('alias_model_id', '!=', reply_model_id),
            ])
            if other_model_aliases:
                is_a_reply = False
                rcpt_tos_valid_localparts = [to for to in rcpt_tos_valid_localparts if to in other_model_aliases.mapped('alias_name')]

        if is_a_reply:
            reply_model_id = self.env['ir.model']._get_id(reply_model)
            dest_aliases = self.env['mail.alias'].search([
                ('alias_name', 'in', rcpt_tos_localparts),
                ('alias_model_id', '=', reply_model_id)
            ], limit=1)

            user_id = self._mail_find_user_for_gateway(email_from, alias=dest_aliases).id or self._uid
            route = self._routing_check_route(
                message, message_dict,
                (reply_model, reply_thread_id, custom_values, user_id, dest_aliases),
                raise_exception=False)
            if route:
                _logger.info(
                    'Routing mail from %s to %s with Message-Id %s: direct reply to msg: model: %s, thread_id: %s, custom_values: %s, uid: %s',
                    email_from, email_to, message_id, reply_model, reply_thread_id, custom_values, self._uid)
                return [route]
            elif route is False:
                return []

        # 2. Handle new incoming email by checking aliases and applying their settings
        if rcpt_tos_localparts:
            # no route found for a matching reference (or reply), so parent is invalid
            message_dict.pop('parent_id', None)

            # check it does not directly contact catchall
            if catchall_alias and all(email_localpart == catchall_alias for email_localpart in email_to_localparts):
                _logger.info('Routing mail from %s to %s with Message-Id %s: direct write to catchall, bounce', email_from, email_to, message_id)
                body = self.env.ref('mail.mail_bounce_catchall')._render({
                    'message': message,
                }, engine='ir.qweb')
                self._routing_create_bounce_email(email_from, body, message, references=message_id, reply_to=self.env.company.email)
                return []

            #geminatecs
            # dest_aliases = self.env['mail.alias'].search([('alias_name', 'in', rcpt_tos_valid_localparts)])
            
            alias_domain_id = self.env['alias.mail'].search([('domain_name','in',email_to_alias_domain_list)])
            dest_aliases = False
            if alias_domain_id:
                dest_aliases = self.env['mail.alias'].search([('alias_domain','in',alias_domain_id.ids),('alias_name', 'in', rcpt_tos_valid_localparts)])
            #geminatecs

            if dest_aliases:
                routes = []
                for alias in dest_aliases:
                    user_id = self._mail_find_user_for_gateway(email_from, alias=alias).id or self._uid
                    route = (alias.sudo().alias_model_id.model, alias.alias_force_thread_id, ast.literal_eval(alias.alias_defaults), user_id, alias)
                    route = self._routing_check_route(message, message_dict, route, raise_exception=True)
                    if route:
                        _logger.info(
                            'Routing mail from %s to %s with Message-Id %s: direct alias match: %r',
                            email_from, email_to, message_id, route)
                        routes.append(route)
                return routes

        # 3. Fallback to the provided parameters, if they work
        if fallback_model:
            # no route found for a matching reference (or reply), so parent is invalid
            message_dict.pop('parent_id', None)
            user_id = self._mail_find_user_for_gateway(email_from).id or self._uid
            route = self._routing_check_route(
                message, message_dict,
                (fallback_model, thread_id, custom_values, user_id, None),
                raise_exception=True)
            if route:
                _logger.info(
                    'Routing mail from %s to %s with Message-Id %s: fallback to model:%s, thread_id:%s, custom_values:%s, uid:%s',
                    email_from, email_to, message_id, fallback_model, thread_id, custom_values, user_id)
                return [route]

        # ValueError if no routes found and if no bounce occured
        raise ValueError(
            'No possible route found for incoming message from %s to %s (Message-Id %s:). '
            'Create an appropriate mail.alias or force the destination model.' %
            (email_from, email_to, message_id)
        )

class AliasMail(models.Model):
    _name = 'alias.mail'
    _rec_name = 'domain_name'
    
    domain_name = fields.Char(string="Domain Name")
    company_id = fields.Many2one('res.company', string="Company")

class Alias(models.Model):
    _inherit = "mail.alias"
    _rec_name = 'alias_name'
    
    alias_domain = fields.Many2one('alias.mail',default=lambda self: self.env["alias.mail"].sudo().search([('company_id','=',self.env.user.company_id.id)],limit=1))
#     name = fields.Char(related='alias_domain.domain_name', store=True)
    
    _sql_constraints = [
        ('alias_unique', 'Check(1=1)', 'Unfortunately this email alias is already used, please choose a unique one')
    ]
    
    def _clean_and_check_unique(self, name):
        """When an alias name appears to already be an email, we keep the local
        part only. A sanitizing / cleaning is also performed on the name. If
        name already exists an UserError is raised. """
        sanitized_name = remove_accents(name).lower().split('@')[0]
        sanitized_name = re.sub(r'[^\w+.]+', '-', sanitized_name)
        
#         catchall_alias = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.alias')
#         bounce_alias = self.env['ir.config_parameter'].sudo().get_param('mail.bounce.alias')
#         domain = [('alias_name', '=', sanitized_name)]
#         if self:
#             domain += [('id', 'not in', self.ids)]
#         if sanitized_name in [catchall_alias, bounce_alias] or self.search_count(domain):
#             raise UserError(_('The e-mail alias is already used. Please enter another one.'))
        
        return sanitized_name
    
    @api.model
    def _clean_and_make_unique(self, name, alias_ids=False):
        # when an alias name appears to already be an email, we keep the local part only
        name = remove_accents(name).lower().split('@')[0]
        name = re.sub(r'[^\w+.]+', '-', name)
        return name
    
    def name_get(self):
        """Return the mail alias display alias_name, including the implicit
           mail catchall domain if exists from config otherwise "New Alias".
           e.g. `jobs@mail.odoo.com` or `jobs` or 'New Alias'
        """
        res = []
        for record in self:
            if record.alias_name and record.alias_domain:
                res.append((record['id'], "%s@%s" % (record.alias_name, record.alias_domain.domain_name)))
            elif record.alias_name:
                res.append((record['id'], "%s" % (record.alias_name)))
            else:
                res.append((record['id'], _("Inactive Alias")))
        return res

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    alias_domain = fields.Many2one('alias.mail',related='alias_id.alias_domain')
    
    @api.model
    def create(self, vals):
        res = super(AccountJournal, self).create(vals)
        if 'alias_domain' in vals:
            if vals.get('alias_domain'):
                res.alias_id.sudo().write({'alias_domain':vals.get('alias_domain')})
                del(vals['alias_domain'])
            else:
                alias = self.env["alias.mail"].sudo().search([('company_id','=',self.env.user.company_id.id)],limit=1)
                if alias:
                    res.alias_id.sudo().write({'alias_domain':alias.id})
        return res
    
    def write(self, vals):
        for journal in self:
            if 'alias_domain' in vals:
                journal.alias_id.sudo().write({'alias_domain':vals.get('alias_domain')})
                if vals.get('alias_domain'):
                    del(vals['alias_domain'])
        return super(AccountJournal, self).write(vals)
    
    
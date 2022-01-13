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
from odoo import _, api, fields, models, modules, tools

class ResCompanyRepMail(models.Model):
    _inherit = 'res.company'

    company_base =fields.Boolean(default=False,string="Company Base")


class MailMailInheritSMTP(models.Model):
    _inherit = 'mail.mail'
    
    @api.model_create_multi
    def create(self, values_list):
        messages = super(MailMailInheritSMTP, self).create(values_list)
        if self.env.user.company_id.company_base == False:
            for message in messages:
                smtp_replay = ''
                catchall = self.env['ir.config_parameter'].sudo().get_param("mail.catchall.alias")
                if not catchall:
                    catchall = 'catchall'
                if message.model:
                    if message.res_id:
                        current_record = self.env[message.model].sudo().search([('id','=',message.res_id)])
                        filters = self.env[message.model]._fields.keys()
                        if 'alias_id' in filters:
                            if current_record.alias_id:
                                if current_record.alias_id.alias_name and current_record.alias_id.alias_domain:
                                    smtp_replay =  '"%s" <%s@%s>' % (current_record.alias_id.alias_name,current_record.alias_id.alias_name,current_record.alias_id.alias_domain.domain_name)
                                if current_record.alias_id.alias_name and not current_record.alias_id.alias_domain:
                                    if 'company_id' in filters and current_record.company_id:
                                        alias_g = self.env['alias.mail'].sudo().search([('company_id','=',current_record.company_id.id)],limit=1)
                                    else:
                                        alias_g = self.env['alias.mail'].sudo().search([('company_id','=',self.env.user.company_id.id)],limit=1)
                                    if alias_g:
                                        smtp_replay =  '"%s" <%s@%s>' % (current_record.alias_id.alias_name,current_record.alias_id.alias_name,alias_g.domain_name)
                                if not current_record.alias_id.alias_name and current_record.alias_id.alias_domain:
                                    if 'company_id' in filters and current_record.company_id:
                                        smtp_replay =  '"%s" <%s@%s>' % (current_record.company_id.name,catchall,current_record.alias_id.alias_domain.domain_name)
                                    else:
                                        smtp_replay =  '"%s" <%s@%s>' % (self.env.user.company_id.name,catchall,current_record.alias_id.alias_domain.domain_name)
                                if not current_record.alias_id.alias_name and not current_record.alias_id.alias_domain:
                                    if 'company_id' in filters and current_record.company_id:
                                        alias_g = self.env['alias.mail'].sudo().search([('company_id','=',current_record.company_id.id)],limit=1)
                                        if alias_g:
                                            smtp_replay =  '"%s" <%s@%s>' % (current_record.company_id.name,catchall,alias_g.domain_name)
                                    else:
                                        alias_g = self.env['alias.mail'].sudo().search([('company_id','=',self.env.user.company_id.id)],limit=1)
                                        if alias_g:
                                            smtp_replay =  '"%s" <%s@%s>' % (self.env.user.company_id.name,catchall,alias_g.domain_name)
                        if not smtp_replay:
                            if 'company_id' in filters and current_record.company_id:
                                if not smtp_replay:
                                    dest_aliases_g = self.env['mail.alias'].sudo().search([
                                        ('alias_name','!=',False),
                                        ('alias_domain','!=',False),
                                        ('alias_domain.company_id', '=', current_record.company_id.id),
                                        ('alias_model_id.model', '=', message.model),
                                    ],limit=1)
                                    if dest_aliases_g and dest_aliases_g.alias_name and dest_aliases_g.alias_domain:
                                        smtp_replay =  '"%s" <%s@%s>' % (dest_aliases_g.alias_name,dest_aliases_g.alias_name,dest_aliases_g.alias_domain.domain_name)
                                
                                if not smtp_replay:
                                    dest_aliases_g = self.env['mail.alias'].sudo().search([
                                        ('alias_name','!=',False),
                                        ('alias_domain','=',False),
                                        ('alias_model_id.model', '=', message.model),
                                    ],limit=1)
                                    if dest_aliases_g and dest_aliases_g.alias_name:
                                        alias_g = self.env['alias.mail'].sudo().search([('company_id','=',current_record.company_id.id)],limit=1)
                                        if alias_g:
                                            smtp_replay = '"%s" <%s@%s>' % (dest_aliases_g.alias_name,dest_aliases_g.alias_name,alias_g.domain_name)
                                
                                if not smtp_replay:
                                    dest_aliases_g = self.env['mail.alias'].sudo().search([
                                        ('alias_name','=',False),
                                        ('alias_domain','!=',False),
                                        ('alias_domain.company_id', '=', current_record.company_id.id),
                                        ('alias_model_id.model', '=', message.model),
                                    ],limit=1)
                                    if dest_aliases_g and dest_aliases_g.alias_domain:
                                        smtp_replay =  '"%s" <%s@%s>' % (current_record.company_id.name,catchall,dest_aliases_g.alias_domain.domain_name)
                                
                                if not smtp_replay:
                                    alias_g = self.env['alias.mail'].sudo().search([('company_id','=',current_record.company_id.id)],limit=1)
                                    if alias_g:
                                        smtp_replay = '"%s" <%s@%s>' % (current_record.company_id.name,catchall,alias_g.domain_name)
                    
                    if not smtp_replay:
                        dest_aliases_g = self.env['mail.alias'].sudo().search([
                            ('alias_name','!=',False),
                            ('alias_domain','!=',False),
                            ('alias_domain.company_id', '=', self.env.user.company_id.id),
                            ('alias_model_id.model', '=', message.model),
                        ],limit=1)
                        if dest_aliases_g and dest_aliases_g.alias_name and dest_aliases_g.alias_domain:
                            smtp_replay =  '"%s" <%s@%s>' % (dest_aliases_g.alias_name,dest_aliases_g.alias_name,dest_aliases_g.alias_domain.domain_name)
                    
                    if not smtp_replay:
                        dest_aliases_g = self.env['mail.alias'].sudo().search([
                            ('alias_name','!=',False),
                            ('alias_domain','=',False),
                            ('alias_model_id.model', '=', message.model),
                        ],limit=1)
                        if dest_aliases_g and dest_aliases_g.alias_name:
                            alias_g = self.env['alias.mail'].sudo().search([('company_id','=',self.env.user.company_id.id)],limit=1)
                            if alias_g:
                                smtp_replay = '"%s" <%s@%s>' % (dest_aliases_g.alias_name,dest_aliases_g.alias_name,alias_g.domain_name)
                    
                    if not smtp_replay:
                        dest_aliases_g = self.env['mail.alias'].sudo().search([
                            ('alias_name','=',False),
                            ('alias_domain','!=',False),
                            ('alias_domain.company_id', '=', self.env.user.company_id.id),
                            ('alias_model_id.model', '=', message.model),
                        ],limit=1)
                        if dest_aliases_g and dest_aliases_g.alias_domain:
                            smtp_replay =  '"%s" <%s@%s>' % (self.env.user.company_id.name,catchall,dest_aliases_g.alias_domain.domain_name)
                
                if not smtp_replay:
                    alias_g = self.env['alias.mail'].sudo().search([('company_id','=',self.env.user.company_id.id)],limit=1)
                    if alias_g:
                        smtp_replay = '"%s" <%s@%s>'  % (self.env.user.company_id.name,catchall,alias_g.domain_name)
                
                print('-mail.mail-',message.reply_to,smtp_replay)
                if smtp_replay:
                    message.reply_to = smtp_replay
        return messages
    
    
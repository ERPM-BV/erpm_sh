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
{
    'name' : 'Mail SMTP and IMAP + Alias Domain By Company Reply-to',
    'version' : '15.0.0.1',
    'author': 'Geminate Consultancy Services',
    'company': 'Geminate Consultancy Services',
    'category': 'sales',
    'website': 'https://www.geminatecs.com/',
    'summary' : 'Mail SMTP and IMAP + Alias Domain By Company Reply-to',
    'description' : """
        Geminate comes with a feature to support multiple domain and multi company reply-to emailing systems in support of 'Mail SMTP and IMAP + Alias Domain By Company' app.
        It supports below listed scenarios,
        If a data record associated with alias and alias having company based domain name configured then alias@company->alias->alias_domain_name will set a reply-to email address.
        If a data record associated with alias but alias doesn't have domain name configured then alias@user->current_company->alias_domain_name will set a reply-to email address.
        If a data record doesn't associate to alias but is attached to a related company then catchall@company->alias->alias_domain_name on reply-to email address.
        If a data record doesn't associate to alias nor attached to related company then catchall@user->current_company->alias->alias_domain_name on reply-to email address.
    """,
    'depends' : ['mail_smtp_imap_by_company'],
    "license": "Other proprietary",
    'installable': True,
    'images': ['static/description/email_reply_to.png'],
    'auto_install': False,
    'application': False,
    'price': 49.99,
    'currency': 'EUR'
}

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
    'name' : 'Mail SMTP and IMAP + Alias Domain By Company Helpdesk',
    'version' : '15.1.1.0',
    'author': 'Geminate Consultancy Services',
    'company': 'Geminate Consultancy Services',
    'category': 'sales',
    'website': 'https://www.geminatecs.com/',
    'summary' : 'Geminate comes with a feature to support company wise multiple alias domains for helpdesk teams which will create tickets from incoming emails when the incoming mail server is configured proper company specific. you can set multiple alias domains and their name in "Helpdesk Team".',
    'description' : """Geminate comes with a feature to support company wise multiple alias domains for helpdesk teams which will create tickets from incoming emails when the incoming mail server is configured proper company specific. you can set multiple alias domains and their name in 'Helpdesk Team'. you can configure multiple email aliases with multiple domains and every email will fetch in the exact destination database table record as per configuration. no limit of single website domain based email aliases.""",
    'depends' : ['mail_smtp_imap_by_company','helpdesk'],
    'data' : [
        'views/alias_mail_view.xml',
    ],
    "license": "Other proprietary",
    'installable': True,
    'images': ['static/description/mail_smtp_imap_by_company_helpdesk.png'],
    'auto_install': False,
    'application': False,
    'price': 49.99,
    'currency': 'EUR'
}

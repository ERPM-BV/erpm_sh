# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Multi Company User Signature",
    'version': '15.0.0.1.1',
    'category': 'Mail',
    'license': 'Other proprietary',
    'summary': "Geminate comes with the feature of mutl company based user email signature where users can configure different email signatures for all the companies which they are allowed to work with either parent or child. so when sending an email out from odoo, it will pick the correct email signature configured under user settings and append that in the email. It helps you to digitize your personalized email signature company specifically where users can easily decide their opinion on which signatures are added for this company.",
    'description': """Geminate comes with the feature of mutl company based user email signature where users can configure different email signatures for all the companies which they are allowed to work with either parent or child. so when sending an email out from odoo, it will pick the correct email signature configured under user settings and append that in the email. It helps you to digitize your personalized email signature company specifically where users can easily decide their opinion on which signatures are added for this company.
        
    """,
    'author': "Geminate Consultancy Services",
    'website': 'http://www.geminatecs.com',
    'depends': ['base', 'mail'],
    'data': [
        "security/ir.model.access.csv",
        "data/mail_data_view.xml",
        "views/multi_companey_view.xml",
    ],
    'images':[
        'static/description/Banner.png'
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 59.99,
    'currency': 'EUR'
}

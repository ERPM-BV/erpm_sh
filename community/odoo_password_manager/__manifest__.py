# -*- coding: utf-8 -*-
{
    "name": "Password Manager",
    "version": "15.0.1.0.9",
    "category": "Extra Tools",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/password-manager-589",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "mail"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings.xml",
        "wizard/bundle_login.xml",
        "wizard/password_generator.xml",
        "views/password_bundle.xml",
        "views/password_key.xml",
        "views/password_tag.xml",
        "wizard/update_password_tag.xml",
        "wizard/update_password_partner.xml",
        "views/res_partner.xml",
        "views/menu.xml",
        "data/data.xml",
        "data/cron.xml"
    ],
    "assets": {
        "web.assets_backend": [
                "odoo_password_manager/static/src/js/pw_password.js",
                "odoo_password_manager/static/src/js/abstract_controller.js",
                "odoo_password_manager/static/src/js/kanban_record.js",
                "odoo_password_manager/static/src/js/password_kanbancontroller.js",
                "odoo_password_manager/static/src/js/password_kanbanmodel.js",
                "odoo_password_manager/static/src/js/password_kanbanrecord.js",
                "odoo_password_manager/static/src/js/password_kanbanrenderer.js",
                "odoo_password_manager/static/src/js/password_kanbanview.js",
                "odoo_password_manager/static/src/js/bundle_password.js",
                "odoo_password_manager/static/src/css/styles.css"
        ],
        "web.assets_qweb": [
                "odoo_password_manager/static/src/xml/*.xml"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "zxcvbn",
                "cryptography"
        ]
},
    "summary": "The tool to safely keep passwords in Odoo for shared use",
    "description": """
For the full details look at static/description/index.html

* Features * 

- Shared use, encryption and protection of passwords
- &lt;i class='fa fa-gears'&gt;&lt;/i&gt; Custom attributes for Odoo passwords 



#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "188.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=103&ticket_version=15.0&url_type_id=3",
}
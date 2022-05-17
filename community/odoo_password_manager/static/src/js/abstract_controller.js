/** @odoo-module **/

import session from "web.session";
import AbstractController from "web.AbstractController";
import rpc from "web.rpc";
import dialogs from "web.view_dialogs";
import { _lt } from "web.core";

AbstractController.include({
    /*
     * Re-write to introduce a password security for certain models
    */
    async _update(state, params) {
        if (state && state.model && ["password.bundle", "password.key", "password.tag", "password.access"].includes(state.model)) {
            var self = this;
            var _super = this._super.bind(this);
            var super_args = arguments;
            return new Promise(function (resolve, reject) {
                resolve(self._checkSecurity(state));
            }).then(function (secCheck) {
                if (secCheck){return _super(...super_args);}
                else {return };
            });                
        }
        else {return this._super(...arguments);}
    },
    /*
     * The method to trigger login dialog if required
    */
    _checkSecurity: function(state) {
        var Defer = $.Deferred();
        var self = this;
        if (["password.bundle", "password.key", "password.tag", "password.access"].includes(state.model)) {
            var resIDs = [];
            var modelName = state.model;
            var viewType = state.viewType;
            if (self.bundle_ids) {
                // for the case bundles comes to us from parent controller
                modelName = "password.bundle";
                resIDs = self.bundle_ids;
                viewType = "form";
            }
            else {
                if (Array.isArray(state.data)) {resIDs = state.data.map(a => a.res_id);}
                else {resIDs = [state.data.id]};
            }
            self._rpc({
                model: "password.bundle",
                method: 'check_action_security',
                args: [modelName, resIDs, viewType],
                context: session.user_context,
            }).then(function (res) {
                if (res) {
                    if (self.confirm_dialog) {
                        // To make sure it is not a duplicated item
                        // We can't just rely upon existing dialog, since controllers are not initiated between
                        // Different objects' views
                        self.confirm_dialog.noreload = true;
                        self.confirm_dialog.close();
                    };
                    var dialog = new LogInDialog(self, {
                        res_model: "bundle.login",
                        title: res[2],
                        view_id: res[1],
                        context: {'default_bundle_id': res[0]},
                        readonly: false,
                        shouldSaveLocally: false,
                        buttons: [
                            {
                                text: (_lt("Log In")),
                                classes: "btn-primary bundle_login",
                                click: function () {
                                    self._onLogIn(dialog).then(function (res) {
                                        if (res) {
                                            Defer.resolve(true);
                                        }
                                    })
                                },
                            },
                        ],
                        related_widget: self,
                    }).open();
                    self.confirm_dialog = dialog;
                }
                else {Defer.resolve(true)}
            });
        }
        else {
            Defer.resolve(true)
        };
        return Defer
    },
    /*
     * The method to call password verify
    */
    _onLogIn: function(dialog) {
        var Defer = $.Deferred();
        var self = this;
        var record = dialog.form_view.model.get(dialog.form_view.handle);
        var bundle = record.data.bundle_id.res_id;
        var password = record.data.password;
        self._rpc({
            model: "password.bundle",
            method: "action_login_bundle",
            args: [[bundle], password],
            context: session.user_context,
        }).then(function (res) {
            if (res) {
                dialog.noreload = true;
                dialog.close();
                self.reload({"controllerState": {"context": session.user_context}});
                Defer.resolve(true);
            }
        });
        return Defer
    },
});

var LogInDialog = dialogs.FormViewDialog.extend({
    /*
     * Re-write to pass widget under which action will be done
    */
    init: function (parent, options) {
        this.related_widget = options.related_widget;
        this._super.apply(this, arguments);
    },
    /*
     * Re-write to the case of mere close > open bundles
    */
    destroy: function (options) {
        this._super.apply(this, arguments);
        var self = this;
        if (!self.noreload) {
            rpc.query({
                model: "password.bundle",
                method: "return_bundles_action",
                args: [],
                context: session.user_context,
            }).then(function (res) {
                self.related_widget.do_action(res);
                self.related_widget.destroy();
            });
        };
    },
});

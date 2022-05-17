/** @odoo-module **/

import KanbanController from "web.KanbanController";
import DataExport from "web.DataExport";
import dialogs from "web.view_dialogs";
import { qweb, _lt } from "web.core";

const PasswordKanbanController = KanbanController.extend({
    events: _.extend({}, KanbanController.prototype.events, {
        "change #passmannsort": "_applyPasswordSorting",
        "click .passmannreverse_sort": "_applyReversePassmannSorting",
        "click .passmannselect_all": "addAll2SelectedPasswords",
        "click .passmannclear": "_clearTags",
        "click .clear_selected_passwords": "clearAllSelectedPasswords",
        "click .password_management_password_selected_row": "_removePasswordSelected",
        "click #add_passmann_tag": "_addRootTag",
        "click .mass_action_button": "_proceedMassAction",
        "click .mass_action_export": "_massActionExport",
        "click .full_view_password": "_openPasswordFullView",
        "click .fa-paste.detail_password_button": "_copy2ClipBoard",
        "click .fa-external-link.detail_password_button": "_onOpenExtUrl",
        "click .fa-eye.detail_password_button": "_onShowHide",
    }),
    jsLibs: [
        '/odoo_password_manager/static/lib/jstree/jstree.js',
    ],
    cssLibs: [
        '/odoo_password_manager/static/lib/jstree/themes/default/style.css',
    ],
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
        select_record: '_passwordSelected',
    }),
    /*
     * Re-write to apply rendering params
    */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.nonavigation_update = false;
        this.selectedRecords = [];
        this.navigationExist = false;
    },
    /*
     * The method to keep required values in self
    */
    _prepareSelf: function() {
        var self = this;
        var Defer = $.Deferred();
        var renderer = self.renderer;
        if (renderer.state.context.all_passwords && renderer.state.context.active_ids
                && renderer.state.context.active_ids.length) {
            this.bundle_ids = renderer.state.context.active_ids;
            this.bundle_id = renderer.state.context.active_ids[0];
            this.bundle_domain = [["bundle_id", "in", renderer.state.context.active_ids]]
            if (!renderer.state.context.default_bundle_id) {
                self.renderer.state.context.params.default_bundle_id = this.bundle_id;
            };
            Defer.resolve();
        }
        else {
            self._rpc({
                model: "password.bundle",
                method: 'return_all_active_bundles',
                args: [],
                context: self.renderer.state.context,
            }).then(function (bundles) {
                if (bundles && bundles.length) {
                    self.bundle_ids = bundles;
                    self.bundle_id = bundles[0];
                    self.bundle_domain = [["bundle_id", "in", bundles]]
                }
                else {
                    self.bundle_domain = [["id", "=", 0]];
                }
                Defer.resolve();
            });
        };
        self.$('.o_content').addClass('password_management_passwords d-flex');
        return Defer;
    },
    /*
     * Re-write to apply required to method params
    */
    async start() {
        var self = this;
        var _super = this._super.bind(this, arguments);
        return $.when(self._prepareSelf()).then(function () {
            return _super();
        });
    },
    /*
     * Re-write to render left navigation panel
    */
    async _update(state, params) {
        var self = this;
        var def = $.Deferred();
        this._super.apply(this, arguments).then(function (res) {
            if (self.navigationExist) {
                def.resolve(res);
            }
            else {
                self._renderNavigationPanel().then(function () {
                    def.resolve(res);
                });
            };
            self.renderer.updateSelection(self.selectedRecords);
        });
        return def
    },
    /*
     *  Re-write to avoid rerendering left navigation panel and to render passwords domain
    */
    async update(params, options = {}) {
        this.nonavigation_update = true;
        params.passwordSystemDomain = this._renderPasswords();
        return this._super.apply(this, arguments);
    },
    /*
     *  Re-write to force reload
    */
    _reloadAfterButtonClick: function (kanbanRecord, params) {
        var self = this;
        $.when(this._super.apply(this, arguments)).then(function () {
            self.reload();
        });
    },
    /*
     * The method to re-order passwords based on selected key
    */
    _applyPasswordSorting: function(event, passed) {
        event.stopPropagation();
        var self = this;
        var sortKey = event.currentTarget.value;
        var data = this.model.get(this.handle);
        var list = this.model.localData[data.id];
        var asc = false;
        if (passed && passed.reverse) {
            if (list.orderedBy.length != 0 && list.orderedBy[0].name == sortKey) {
                asc = list.orderedBy[0].asc;
            }
            else {
                asc = true;
            };
        };
        // To hack default 'desc' instead of 'asc'
        list.orderedBy = [];
        list.orderedBy.push({name: sortKey, asc: asc});
        this.model.setSort(data.id, sortKey).then(function () {
            self.reload({});
        });
    },
    /*
     * The method to reverse the sorting
    */
    _applyReversePassmannSorting: function(event) {
        event.stopPropagation();
        this.$("#passmannsort").trigger("change", {"reverse": true});
    },
    /*
     * The method to retrieve tags for a current user
    */
    _renderTags: function () {
        var self = this;
        var def = $.Deferred();
        self.$('#password_tags').jstree('destroy');
        self._rpc({
            model: "password.tag",
            method: 'return_nodes',
            args: [this.bundle_ids],
            context: self.renderer.state.context,
        }).then(function (availableTags) {
            var jsTreeOptions = {
                'core' : {
                    'themes': {'icons': false},
                    "multiple" : true,
                    'check_callback' : true,
                    'data': availableTags,
                    "strings": {"New node": _lt('New Tag'),}
                },
                "plugins" : [
                    "contextmenu",
                    "checkbox",
                    "state",
                    "search",
                ],
                "state" : { "key" : "password_tags" },
                "checkbox" : {
                    "three_state" : false,
                    "cascade": "down",
                    "tie_selection" : false,
                },
            };
            if (self.is_action_enabled("create")) {
                jsTreeOptions.plugins = [
                    "checkbox",
                    "contextmenu",
                    "dnd",
                    "state",
                    "search",
                ];
                jsTreeOptions.contextmenu = {
                    "select_node": false,
                    "items": function($node) {
                        var tree = $("#password_tags").jstree(true);
                        return {
                            "Create": {
                                "separator_before": false,
                                "separator_after": false,
                                "label": _lt("Create"),
                                "action": function (obj) {
                                    self._checkSecurity(self.initialState).then(function (res) {
                                        $node = tree.create_node($node);
                                        tree.edit($node);
                                    })
                                }
                            },
                            "Rename": {
                                "separator_before": false,
                                "separator_after": false,
                                "label": _lt("Rename"),
                                "action": function (obj) {
                                    self._checkSecurity(self.initialState).then(function (res) {
                                        tree.edit($node);
                                    });
                                }
                            },
                            "Edit": {
                                "separator_before": false,
                                "separator_after": false,
                                "label": _lt("Edit"),
                                "action": function (obj) {
                                    self._checkSecurity(self.initialState).then(function (res) {
                                        var resId = parseInt($node.id);
                                        self._onEditTagForm(resId);
                                    });
                                }
                            },
                            "Remove": {
                                "separator_before": false,
                                "separator_after": false,
                                "label": _lt("Archive"),
                                "action": function (obj) {
                                    self._checkSecurity(self.initialState).then(function (res) {
                                        tree.delete_node($node);
                                    });
                                }
                            },
                        };
                    },
                };
            };
            var ref = self.$('#password_tags').jstree(jsTreeOptions);
            if (self.is_action_enabled("create")) {
                self.$('#password_tags').on("rename_node.jstree", self, function (event, data) {
                    // This also includes 'create' event. Since each time created, a node is updated then
                    self._updateNode(event, data, 'password.tag', false);
                });
                self.$('#password_tags').on("move_node.jstree", self, function (event, data) {
                    self._updateNode(event, data, 'password.tag', true);
                });
                self.$('#password_tags').on("delete_node.jstree", self, function (event, data) {
                    self._deleteNode(event, data, 'password.tag');
                });
                self.$('#password_tags').on("copy_node.jstree", self, function (event, data) {
                    self._updateNode(event, data, 'password.tag', true);
                });
            };
            self.$('#password_tags').on("state_ready.jstree", self, function (event, data) {
                self.reload({"domain": self.model.get(self.handle).domain});
                // We register 'checks' only after restoring the tree to avoid multiple checked events
                self.$('#password_tags').on("check_node.jstree uncheck_node.jstree", self, function (event, data) {
                    self.reload();
                })
            });
            def.resolve();
        });
        return def
    },
    /*
     * The method to render left navigation panel
    */
    _renderNavigationPanel: function () {
        var self = this;
        var scrollTop = self.$('.password_management_navigation_panel').scrollTop();
        self.$('.password_management_navigation_panel').remove();
        var navigationElements = {};
        var $navigationPanel = $(qweb.render('PasswordNavigationPanel', navigationElements));
        self.$('.o_content').prepend($navigationPanel);
        var def = $.Deferred();
        self._renderTags().then(function () {
            def.resolve()
        });
        self.$('.password_management_navigation_panel').scrollTop(scrollTop || 0);
        self.navigationExist = true;
        return def;
    },
    /*
     *  The method to render right navigation panel
    */
    _renderRightNavigationPanel: function () {
        var self = this;
        self._checkSecurity(self.initialState).then(function (res) {
            var scrollTop = self.$('.password_management_right_navigation_panel').scrollTop();
            self.$('.password_management_right_navigation_panel').remove();
            var selectedRecords = self.selectedRecords;
            if (selectedRecords.length) {
                self._rpc({
                    model: "password.key",
                    method: 'return_selected_passwords',
                    args: [self.selectedRecords],
                    context: self.renderer.state.context,
                }).then(function (passwords) {
                    var $navigationPanel = $(qweb.render(
                        'PasswordRightNavigationPanel', {
                            "passwords": passwords[0],
                            "count_passwords": passwords[0].length,
                            "mass_actions": passwords[1],
                            "export_conf": passwords[2],
                            "single_password": passwords[3],
                        })
                    );
                    self.$('.o_content').append($navigationPanel);
                    self.$('.password_management_right_navigation_panel').scrollTop(scrollTop || 0);
                });
            }
        });
    },
    /*
     * The method to prepare new filters and trigger passwords rerender
    */
    _renderPasswords: function () {
        this._checkSecurity(this.initialState);
        var bundle_domain = this.bundle_domain;
        var self = this;
        var bdomain = [...bundle_domain];
        var refT = self.$('#password_tags').jstree(true);
        if (refT) {
            var checkedTags = refT.get_checked(),
                tagsLength = checkedTags.length;
            if (tagsLength != 0) {
                var iterator = 0;
                while (iterator != tagsLength-1) {
                    bdomain.push('|');
                    iterator ++;
                }
                _.each(checkedTags, function (tag) {
                    if (tag.length) {
                        bdomain.push(['tag_ids', 'in', parseInt(tag)]);
                    }
                });
            };
        };
        return bdomain;
    },
    /*
     * The method clear all checked tags
    */
    _clearTags: function(event) {
        var self = this;
        var ref = self.$('#password_tags').jstree(true);
        ref.uncheck_all();
        ref.save_state()
        self.reload();
    },
    /*
     * The method to trigger update of jstree node
    */
    _updateNode: function (event, data, model, position) {
        var self = this;
        if (position) {
            position = parseInt(data.position);
        }
        if (data.node.id === parseInt(data.node.id).toString()) {
            self._rpc({
                model: model,
                method: 'update_node',
                args: [[parseInt(data.node.id)], data.node, position],
                context: self.renderer.state.context,
            });
        }
        else {
            var thisElId = data.node.id;
            self._rpc({
                model: model,
                method: 'create_node',
                args: [data.node, self.bundle_id],
                context: self.renderer.state.context,
            }).then(function (new_id) {
                // To apply real ids, not jstree ids
                if (model == "password.tag") {
                    self._renderTags();
                };
            });
        };
    },
    /*
     * The method to trigger unlink of jstree node 
    */
    _deleteNode: function (event, data, model) {
        var self = this;
        self._rpc({
            model: model,
            method: 'delete_node',
            args: [[parseInt(data.node.id)]],
            context: self.renderer.state.context,
        });
    },
    /*
     * The method to add a new root tag
    */
    _addRootTag: function(event) {
        var self = this;
        self._checkSecurity(self.initialState).then(function (res) {
            var ref = self.$('#password_tags').jstree(true),
                sel = ref.get_selected();
            sel = ref.create_node('#');
            if(sel) {
                ref.edit(sel);
            }
        });
    },
    /*
     * The method to open tag edit form
    */
    _onEditTagForm: function(resID) {
        var self = this;
        this._checkSecurity(this.initialState).then(function (res) {
            self._rpc({
                model: "password.tag",
                method: 'return_edit_form',
                args: [[]],
                context: self.renderer.state.context,
            }).then(function (view_id) {
                var onSaved = function(record) {
                    self._renderTags();
                };
                new dialogs.FormViewDialog(self, {
                    res_model: "password.tag",
                    title: _lt("Edit Tag"),
                    view_id: view_id,
                    res_id: resID,
                    readonly: false,
                    shouldSaveLocally: false,
                    on_saved: onSaved,
                    context: self.renderer.state.context,
                }).open();
            });
        });
    },
    /*
     * The method to process password selected
    */
    _passwordSelected: function(event) {
        event.stopPropagation();
        var eventData = event.data;
        var addToSelection = eventData.selected;
        if (addToSelection) {
            this.selectedRecords.unshift(eventData.resID);
        }
        else {
            this.selectedRecords = _.without(this.selectedRecords, eventData.resID);
        };
        this._renderRightNavigationPanel();
    },
    /*
     * The method to add all passwords found to the selection
    */
    addAll2SelectedPasswords: function(event) {
        event.stopPropagation();
        var self = this;
        var alreadySelected = this.selectedRecords;
        var data = this.model.get(this.handle);
        var list = this.model.localData[data.id];
        // We can't use res_ids since it only the first page --> so we rpc search
        this._rpc({
            model: "password.key",
            method: 'rerurn_all_pages_ids',
            args: [alreadySelected, list.domain],
            context: self.renderer.state.context,
        }).then(function (resIDS) {
            self.selectedRecords = resIDS;
            self.renderer.updateSelection(resIDS);
            self._renderRightNavigationPanel();
        });
    },
    /*
     * The method to clear all selected passwords
    */
    clearAllSelectedPasswords: function(event) {
        event.stopPropagation();
        this.selectedRecords = [];
        this.renderer.updateSelection(this.selectedRecords);
        this._renderRightNavigationPanel();
    },
    /*
     * The method to remove this password from selection
    */
    _removePasswordSelected: function(event) {
        event.stopPropagation();
        var resID = parseInt(event.currentTarget.id);
        this.selectedRecords = _.without(this.selectedRecords, resID);
        this.renderer.updateSelection(this.selectedRecords);
        this._renderRightNavigationPanel();
    },
    /*
     * The method to process mass action event
    */
    _proceedMassAction: function(event) {
        event.stopPropagation();
        var self = this;
        this._checkSecurity(this.initialState).then(function (res){
            var actionID = parseInt(event.currentTarget.id);
            self._rpc({
                model: "password.key",
                method: "proceed_mass_action",
                args: [self.selectedRecords, actionID],
                context: self.renderer.state.context,
            }).then(function (res) {
                if (!res) {
                    self.reload();
                }
                else if (res.view_id) {
                    var onSaved = function(record) {
                        self.reload();
                    };
                    new dialogs.FormViewDialog(self, {
                        res_model: res.res_model,
                        context: {'default_passwords': self.selectedRecords.join()},
                        title: res.display_name,
                        view_id: res.view_id,
                        readonly: false,
                        shouldSaveLocally: false,
                        on_saved: onSaved,
                    }).open();
                }
                else if (res.action) {
                    self.do_action(
                        res.action, 
                        {on_close: () => self.reload()}
                    );
                }
                else {
                    self.reload();
                }
            });
        });
    },
    /*
     * The method to handle click to export records
    */
    _massActionExport: function(event) {
        var self = this;
        this._checkSecurity(this.initialState).then(function (res) {
            var record = self.model.get(self.handle);
            var ExportFields = ["name", "user_name", "password", "email", "link_url"]
            new DataExport(self, record, ExportFields, self.renderer.state.groupedBy, self.getActiveDomain(), self.selectedRecords).open();
        });
    },
    /*
     * The method is required to construct export popup
    */
    getActiveDomain: function () {
        return [["id", "in", this.selectedRecords]];
    },
    /*
     * Handle click to open password form view
    */
    _openPasswordFullView: function(event) {

        var self = this;
        self._checkSecurity(self.initialState).then(function (res) {
            var resID = parseInt(event.target.id);
            self._rpc({
                model: "password.key",
                method: 'return_edit_form',
                args: [],
                context: self.renderer.state.context,
            }).then(function (view_id) {
                var onSaved = function(record) {
                    self._renderTags();
                    self._renderRightNavigationPanel();
                };
                new dialogs.FormViewDialog(self, {
                    res_model: "password.key",
                    title: _lt("Edit Password"),
                    view_id: view_id,
                    res_id: resID,
                    readonly: false,
                    shouldSaveLocally: false,
                    on_saved: onSaved,
                    context: self.renderer.state.context,
                }).open();
            });
        });
    },
    /*
     * The method to copy input value for cliboard
    */
    _copy2ClipBoard: function(event) {
        var self = this;
        this._checkSecurity(this.initialState).then(function (res) {
            var copiedValue = event.target.id;
            var dummy = document.createElement("input");
            $(".overall_passwords_selection").append(dummy);
            dummy.setAttribute('value', copiedValue);
            dummy.setAttribute('class', "empty_height");
            if (navigator.userAgent.match(/ipad|ipod|iphone/i)) {
                dummy.setAttribute("contenteditable", "true");
                dummy.setAttribute("readOnly", "false");
                var range = document.createRange();
                range.selectNodeContents(dummy);
                var sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
                dummy.setSelectionRange(0, 999999);
            } else {
                dummy.select();
            }
            document.execCommand("copy");
            dummy.remove();
        });
    },
    /*
     * The method to copy value to clipboard
    */
    _onOpenExtUrl: function(event) {
        this._checkSecurity(this.initialState).then(function (res) {
            var linkURL = event.target.id;
            window.open(linkURL, '_blank');
        });
    },
    /*
     * The method to copy value to clipboard
    */
    _onShowHide: function(event) {
        this._checkSecurity(this.initialState).then(function (res) {
            var pwInput = $(event.target).parent().parent().find("#pw_input_in")[0];
            if (pwInput.type == "password") {pwInput.type = "text"}
            else {pwInput.type = "password"}
        });
    },
});

export default PasswordKanbanController;

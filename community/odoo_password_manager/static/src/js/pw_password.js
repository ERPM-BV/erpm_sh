/** @odoo-module **/

import basicFields from "web.basic_fields";
import fieldRegistry from "web.field_registry";
import session from "web.session";
import dialogs from "web.view_dialogs";
import { _lt } from "web.core";


var UnclickablePriority = basicFields.PriorityWidget.extend({
    className: 'o_field_pw_priority o_priority',
    /*
     *  Re-write since no action is requried
    */
    _onClick: function (event) {
        event.preventDefault();
        event.stopPropagation();
    },
    /*
     * Re-write since no action is requried
    */
    _onMouseOver: function (event) {},
    /*
     * Re-write since no action is requried
    */
    _onMouseOut: function (event) {
    },
    /*
     *  Re-write to adapt styles
    */
    _renderStar: function (tag, isFull, index, tip) {
        return $(tag)
            .attr('title', tip)
            .attr('aria-label', tip)
            .attr('data-index', index)
            .addClass('o_priority_star fa starsmall')
            .toggleClass('fa-star', isFull)
            .toggleClass('fa-star-o', !isFull);
    },
});

var pwPassword = basicFields.FieldChar.extend({
    className: 'o_field_password',
    /*
     * Re-write to render functional buttons
     * IMPORTANT: buttons are available only in edit mode
    */
    _renderEdit: function () {
        var def = this._super.apply(this, arguments);
        this.$input[0].type = "password"
        this.$el = this.$el.add(this._renderShowHide());
        this.$el = this.$el.add(this._renderCopy());
        this.$el = this.$el.add(this._renderGenerator());
        return def
    },
    /*
     * Re-write to show stars by default instead of a real password
    */    
    _renderReadonly: function () {
        this.$el.text("*****");
    },
    /*
     * The method to render password functional buttons
    */
    _renderShowHide: function() {
        return $('<button>', {
                        type: 'button',
                        'class': 'show_hide_password fa fa-eye btn btn-link',
               }).on('click', this._onShowHidePassword.bind(this));
    },
    /*
     * The method to render password functional buttons
    */
    _renderCopy: function() {
        return $('<button>', {
                        type: 'button',
                        'class': 'clipboard_password fa fa-paste btn btn-link',
               }).on('click', this._onCopy2Clipboard.bind(this));
    },
    /*
     * The method to render password functional buttons
    */
    _renderGenerator: function() {
        return $('<button>', {
                        type: 'button',
                        'class': 'generate_password fa fa-rotate-left btn btn-link',
               }).on('click', this._onGeneratePassword.bind(this));
    },
    /*
     * The method to update visibility option
    */
    _onShowHidePassword: function(event) {
        event.preventDefault();
        if (this.$input[0].type == "password") {this.$input[0].type = "text"}
        else {this.$input[0].type = "password"}
    },
    /*
     * The method to copy value to clipboard 
    */
    _onCopy2Clipboard: function(event) {                   
        var nameToCopy = this.$input[0].value;        
        var dummy = document.createElement("input");
        this.$el[1].append(dummy);
        dummy.setAttribute('value', nameToCopy);
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
    },
    /*
     * The method to open the password generator wizard
    */
    _onGeneratePassword(event) {
        var self = this;
        const pg_dialog = new dialogs.FormViewDialog(this, {
            res_model: "password.generator",
            context: session.user_context,
            title: _lt("Password Generator"),
            readonly: false,
            shouldSaveLocally: false,
            size: "small",
            buttons: [
                {
                    text: (_lt("Generate Password")),
                    classes: "btn-primary generate_pw_button",
                    click: function () {
                        pg_dialog._save().then(
                            self._onGeneratePasswordSave(pg_dialog)
                        );
                    },
                },
                {
                    text: (_lt("Discard")),
                    classes: "btn-secondary o_form_button_cancel",
                    close: true,
                },
            ],
        }).open();
    },
    /*
     * The method to generate and update password
    */
    async _onGeneratePasswordSave(pg_dialog) {
        var self = this;
        const record = pg_dialog.form_view.model.get(pg_dialog.form_view.handle);
        const pwLen = record.data.pwlength;
        const pwCharset = record.data.pwcharset;
        const res = await this._rpc({
            model: "password.key",
            method: "generate_password_passlib",
            args: [pwLen, pwCharset],
            context: session.user_context,
        })
        this._setValue(res);
        this.$input[0].value = res;
        this.trigger_up('field_changed', {
            dataPointID: self.dataPointID,
            changes: {"confirm_password": res},
            viewType: self.viewType,
        });
        pg_dialog.close();
    },
});

var copyClipBoardWidget = basicFields.FieldChar.extend({
    className: 'o_field_copy_clipboard',
    /*
     * Re-write to render functional buttons
     * IMPORTANT: buttons are available only in edit mode
    */
    _renderEdit: function () {
        var def = this._super.apply(this, arguments);
        this.$el = this.$el.add(this._renderCopy());
        return def
    },
    /*
     * The method to render password functional buttons
    */
    _renderCopy: function() {
        return $('<button>', {
                        type: 'button',
                        'class': 'show_hide_password fa fa-paste btn btn-link',
               }).on('click', this._onCopy2Clipboard.bind(this));
    },
    /*
     * The method to copy value to clipboard
    */
    _onCopy2Clipboard: function(event) {                   
        var nameToCopy = this.$input[0].value;        
        var dummy = document.createElement("input");
        this.$el[1].append(dummy);
        dummy.setAttribute('value', nameToCopy);
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
    },
});

var copyClipBoardUrlWidget = copyClipBoardWidget.extend({
    className: 'o_field_copyurl_clipboard',
    /*
     * Re-write to render functional buttons
     * IMPORTANT: buttons are available only in edit mode
    */
    _renderEdit: function () {
        var def = this._super.apply(this, arguments);
        this.$el = this.$el.add(this._renderUrl());
        return def
    },
    /*
     * The method to open url from value
    */
    _renderUrl: function() {
        return $('<button>', {
                        type: 'button',
                        'class': 'clipboard_password fa fa-external-link btn btn-link',
               }).on('click', this._onOpenLink.bind(this));
    },
    /*
     * The method to copy value to clipboard
    */
    _onOpenLink: function(event) {
        var linkURL = this.$input[0].value;
        window.open(linkURL, '_blank');
    },
});


fieldRegistry.add('pwPassword', pwPassword);
fieldRegistry.add('copyClipBoardWidget', copyClipBoardWidget);
fieldRegistry.add('copyClipBoardUrlWidget', copyClipBoardUrlWidget);
fieldRegistry.add('UnclickablePriority', UnclickablePriority);

export default {
    pwPassword: pwPassword,
    copyClipBoardWidget: copyClipBoardWidget,
    copyClipBoardUrlWidget: copyClipBoardUrlWidget,
    UnclickablePriority: UnclickablePriority,
};

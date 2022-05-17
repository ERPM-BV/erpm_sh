/** @odoo-module **/

import basicFields from "web.basic_fields";
import fieldRegistry from "web.field_registry";

var bundlePassword = basicFields.FieldChar.extend({
    className: 'o_field_password',
    /*
     * Re-write to render functional buttons
    */
    _renderEdit: function () {
        const def = this._super.apply(this, arguments);
        this.$input[0].type = "password"
        this.$el = this.$el.add(this._renderShowHide());
        return def
    },
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
     * The method to update visibility option
    */
    _onShowHidePassword: function(event) {
        event.preventDefault();
        if (this.$input[0].type == "password") {this.$input[0].type = "text"}
        else {this.$input[0].type = "password"}
    },
    /*
     * The method to process the enter key up
    */
    _onKeydown: function(event) {
        this._super.apply(this, arguments);
        if (event.keyCode === 13) {
        	this._doAction().then(function (res) {
        		$(".bundle_login").click();
        	});               
        };
    },

});

fieldRegistry.add('bundlePassword', bundlePassword);

export default bundlePassword;

/** @odoo-module **/

import KanbanModel from "web.KanbanModel";

const PasswordKanbanModel = KanbanModel.extend({
    /*
     * Re-write to explicitly retrieve passwordSystemDomain
    */
    reload: function (id, options) {
        options = options || {};
        var element = this.localData[id];
        var searchDomain = options.domain || element.searchDomain || [];
        element.searchDomain = options.searchDomain = searchDomain;
        if (options.passwordSystemDomain !== undefined) {
            options.domain = searchDomain.concat(options.passwordSystemDomain);
        };
        return this._super.apply(this, arguments)
    },
});

export default PasswordKanbanModel;

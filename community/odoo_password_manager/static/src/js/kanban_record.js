/** @odoo-module **/

import KanbanRecord from "web.KanbanRecord";

KanbanRecord.include({
    /*
     * The method to open passwords instead of bundle form
    */
    _openRecord: function () {
        if (this.modelName === "password.bundle" && this.$(".o_password_kanban_boxes a").length) {
            this.$(".o_password_kanban_boxes a").first().click();
        } else {
            this._super.apply(this, arguments);
        }
    },
});

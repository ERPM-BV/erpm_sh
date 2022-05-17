/** @odoo-module **/

import PasswordKanbanRecord from "@odoo_password_manager/js/password_kanbanrecord";
import KanbanRenderer from "web.KanbanRenderer";

const PasswordKanbanRenderer = KanbanRenderer.extend({
    config: _.extend({}, KanbanRenderer.prototype.config, {
        KanbanRecord: PasswordKanbanRecord,
    }),
    /*
     * Re-write to keep selected passwords when switching between pages and filters
    */
    updateSelection: function (selectedRecords) {
        _.each(this.widgets, function (widget) {
            var selected = _.contains(selectedRecords, widget.id);
            widget._updateRecordView(selected);
        });
    },
});

export default PasswordKanbanRenderer;

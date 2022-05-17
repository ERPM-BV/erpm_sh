/** @odoo-module **/

import KanbanRecord from "web.KanbanRecord";

const PasswordKanbanRecord = KanbanRecord.extend({
    events: _.extend({}, KanbanRecord.prototype.events, {
        'click .password_select': '_passwordSelect',
    }),
    /*
     * The method to pass selection to the controller
    */
    _updateSelect: function (event, selected) {
        this.trigger_up('select_record', {
            originalEvent: event,
            resID: this.id,
            selected: selected,
        });
    },
    /*
     * The method to mark the password selected / disselected in the interface
    */
    _updateRecordView: function (select) {
        var kanbanCard = this.$el;
        var checkBox = this.$el.find(".password_select");
        if (select) {
            checkBox.removeClass("fa-square-o");
            checkBox.addClass("fa-check-square-o");
            kanbanCard.addClass("passmannkanabanselected");
        }
        else {
            checkBox.removeClass("fa-check-square-o");
            checkBox.addClass("fa-square-o");
            kanbanCard.removeClass("passmannkanabanselected");
        };
    },
    /*
     * The method to add to / remove from selection
    */
    _passwordSelect: function (event) {
        event.preventDefault();
        event.stopPropagation();
        var checkBox = this.$el.find(".password_select");
        if (checkBox.hasClass("fa-square-o")) {
            this._updateRecordView(true)
            this._updateSelect(event, true);
        }
        else {
            this._updateRecordView(false);
            this._updateSelect(event, false);
        }
    },
    /*
     * Re-write to make selection instead of opening a record
    */
    _openRecord: function (real) {
        this.$('.password_select').click();
    },
});

export default PasswordKanbanRecord;

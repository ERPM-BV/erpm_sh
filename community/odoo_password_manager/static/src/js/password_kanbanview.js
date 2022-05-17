/** @odoo-module **/

import PasswordKanbanController from "@odoo_password_manager/js/password_kanbancontroller";
import PasswordKanbanModel from "@odoo_password_manager/js/password_kanbanmodel";
import PasswordKanbanRenderer from "@odoo_password_manager/js/password_kanbanrenderer";
import KanbanView from "web.KanbanView";
import viewRegistry from 'web.view_registry';
import { _lt } from "web.core";

const PasswordKanbanView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Renderer: PasswordKanbanRenderer,
        Controller: PasswordKanbanController,
        Model: PasswordKanbanModel,
    }),
    display_name: _lt("Password Manager"),
    groupable: false,
});

viewRegistry.add("password_kanban", PasswordKanbanView);

export default PasswordKanbanView;

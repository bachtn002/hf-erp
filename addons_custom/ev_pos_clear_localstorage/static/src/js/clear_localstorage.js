odoo.define('ev_pos_clear_localstorage.ClearLocalStorage', function (require) {
    "use strict";

    var KanbanRecord = require('web.KanbanRecord');

    KanbanRecord.include({
        events: _.extend({}, KanbanRecord.prototype.events, {
            'click .oe_clear_localstorage': '_onCLearLocalStorage',
        }),

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * Clear localstorage when click open new pos session
         *
         * @private
         * @param {MouseEvent} ev Click event
         */
        _onCLearLocalStorage: function (ev) {
            ev.preventDefault();
            var arr = []; // Array to hold the keys
            // Iterate over localStorage and insert the keys that meet the condition into arr
            for (let i = 0; i < localStorage.length; i++) {
                if (localStorage.key(i).substring(0, 14) === 'openerp_pos_db') {
                    arr.push(localStorage.key(i));
                }
            }

            // Iterate over arr and remove the items by key
            for (let i = 0; i < arr.length; i++) {
                localStorage.removeItem(arr[i]);
            }
        },
    });

    return KanbanRecord;

    });

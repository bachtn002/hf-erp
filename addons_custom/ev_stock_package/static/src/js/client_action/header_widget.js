odoo.define('ev_stock_package.HeaderWidget', function (require) {
'use strict';

var Widget = require('web.Widget');

var HeaderWidget = Widget.extend({
    'template': 'stock_package_transfer_barcode_header_widget',
    // events: {
    //     'click .o_exit': '_onClickExit',
    // },

    init: function (parent) {
        this._super.apply(this, arguments);
        this.title = parent.title;
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handles the click on the `exit button`.
     *
     * @private
     * @param {MouseEvent} ev
     */
    // _onClickExit: function (ev) {
    //     ev.stopPropagation();
    //     this.trigger_up('exit');
    // },
});

return HeaderWidget;

});

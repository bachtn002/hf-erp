odoo.define('ev_stock_package.MainMenu', function (require){
"use strict";
const MainMenu = require('stock_barcode.MainMenu').MainMenu;

MainMenu.include({
    events: Object.assign({}, MainMenu.prototype.events, {
        'click .button_package_transfers': '_onClickPackageTransfer',
    }),

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------
    _onClickPackageTransfer: function(){
        this.do_action('ev_stock_transfer.action_stock_transfer_from')
    }
})

})
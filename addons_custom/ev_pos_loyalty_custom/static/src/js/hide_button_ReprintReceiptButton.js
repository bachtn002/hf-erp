odoo.define('ev_pos_loyaty_custom.ReprintReceiptButtonHide', function (require) {
    "use strict"

    const OrderManagementScreen = require('point_of_sale.OrderManagementScreen');
    const ReprintReceiptButton = require('point_of_sale.ReprintReceiptButton')
    OrderManagementScreen.addControlButton({
        component: ReprintReceiptButton,
        condition: function () {
            return false;
        },
        position: ['replace', 'ReprintReceiptButton'],
    });
});
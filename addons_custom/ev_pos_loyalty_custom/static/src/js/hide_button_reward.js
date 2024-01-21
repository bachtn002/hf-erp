odoo.define('ev_pos_loyaty_custom.RewardButtonHide', function (require) {
    "use strict"

    const ProductScreen = require('point_of_sale.ProductScreen');
    const RewardButton = require('pos_loyalty.RewardButton')

    ProductScreen.addControlButton({
        component: RewardButton,
        condition: function () {
            return false;
        },
        position: ['replace', 'RewardButton'],
    });
});
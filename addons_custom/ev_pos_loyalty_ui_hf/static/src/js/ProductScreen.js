odoo.define('ev_pos_loyalty_ui_hf.ProductScreenLoyalty', function (require) {
    'use strict';

    const {useState} = owl.hooks;
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');


    let ProductScreenLoyalty = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
            }

            async _updateSelectedOrderline(event) {
                super._updateSelectedOrderline(event);
                let order = this.env.pos.get_order();
                let selectedLine = order.get_selected_orderline();
                if (selectedLine && selectedLine.reward_custom_id === 'reward') {
                    if (event.detail.buffer > 1) {
                        order.remove_orderline(selectedLine);
                    }
                    if (event.detail.buffer < 1) {
                        order.remove_orderline(selectedLine);
                    }
                }
            }
        }
    Registries.Component.extend(ProductScreen, ProductScreenLoyalty);

    return ProductScreen;
})
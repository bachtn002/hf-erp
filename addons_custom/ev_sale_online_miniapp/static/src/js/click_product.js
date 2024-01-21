odoo.define('ev_sale_online_miniapp.ProductScreenClickProduct', function (require) {
    'use strict'

    const ProductScreen = require('ev_promotion_voucher.PromotionVoucherProductScreen')
    const Registries = require('point_of_sale.Registries')

    let ProductScreenClickProduct = ProductScreen => class extends ProductScreen {
        async _clickProduct(event) {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            if (channel_current.length > 0) {
                let is_not_allow_editing = channel_current[0]['is_not_allow_editing']

                return this.env.pos.get_order().sale_online ? (() => {
                    if (this.env.pos.get_order().is_created_by_api) {
                        return
                    } else if (is_not_allow_editing) {
                        return
                    } else {
                        this._removePromotionAppliedProd()
                    }
                })() : super._clickProduct(event)

            } else {
                super._clickProduct(event)
            }
        }


        _removePromotionAppliedProd() {
            this.env.pos.removePromotionsApplied()
            super._clickProduct(event)
        }

        handleOnClickSelect(ev, promotions) {
            this.generatePromotions();
            super.handleOnClickSelect(ev, promotions);
        }
    }

    Registries.Component.extend(ProductScreen, ProductScreenClickProduct)
    return ProductScreen
})
odoo.define('ev_pos_promotion.ProductScreenCustom', function (require) {
    "use strict"
    const core = require('web.core');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const _t = core._t;

    let ProductScreenCustom = ProductScreen =>
        class extends ProductScreen {
            async _onClickPay() {
                // let promotions = this.env.pos.getValidPromotions(null, true);
                let promotions_all = this.env.pos.getValidPromotions(null, true);
                let promotions = [];
                promotions_all.forEach((pro) => {
                    if (!pro.check_promotion) {
                        promotions.push(pro)
                    }
                })
                if (promotions.length > 0) {
                    let props = {
                        title: _t('Confirm payment'),
                        body: _t('Apply all promotions or selected promotion'),
                        confirmText: _t('Apply all'),
                        cancelText: _t('Cancel')
                    }
                    const {applyAll, applySelected} =
                        await this.showPopup('ConfirmPaymentPopup', props);
                    if (applyAll) {
                        // kiểm tra CTKM có dùng mã hay k
                        let promotions_all = this.env.pos.getValidPromotions(null, true);
                        let promotions = [];
                        promotions_all.forEach((pro) => {
                            if (!pro.check_promotion) {
                                promotions.push(pro)
                            }
                        })
                        this.env.pos.removePromotionsApplied();
                        this.env.pos.applyPromotions(promotions);
                        this.generatePromotions();
                        this.showScreen('PaymentScreen');
                    } else if (applySelected) {
                        this.showScreen('PaymentScreen');
                    }
                } else {
                    super._onClickPay();
                }
            }
        };

    Registries.Component.extend(ProductScreen, ProductScreenCustom);

    return ProductScreen;
});
odoo.define('ev_promotion_voucher_custom.ProductScreenCustom', function (require) {
    "use strict"
    const core = require('web.core');
    const ProductScreenCustom = require('ev_pos_ConfirmPaymentPopup_custom.ProductScreenCustom');
    const Registries = require('point_of_sale.Registries');
    const _t = core._t;

    let ProductScreenPromotion = ProductScreenCustom =>
        class extends ProductScreenCustom {
            async _onClickPay() {
                let promotions_all = this.env.pos.getValidPromotions(null, true);
                let promotions = [];
                promotions_all.forEach((pro) => {
                    if (!pro.check_promotion) {
                        promotions.push(pro)
                    }
                });
                let x_show_popup_payment_confirm = this.env.pos.config.x_show_popup_payment_confirm;
                if (x_show_popup_payment_confirm) {
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
                            const orderlines = this.currentOrder.orderlines;
                            let promotions_code = []
                            const map_code_promotion_id = new Map()
                            // xóa giá phân bổ khi xóa CTKM
                            orderlines.forEach((line) => {
                                line.x_is_price_promotion = undefined;
                                line.x_product_promotion = undefined;
                            })
                            var uniq_promotions_id = [];
                            orderlines.forEach((line) => {
                                if (line.promotion_id && line.promotion_code && !uniq_promotions_id.includes(line.promotion_id)) {
                                    let promotion_after = self.posmodel.getPromotionById(line.promotion_id);
                                    promotions_code.push(promotion_after)
                                    uniq_promotions_id.push(line.promotion_id)
                                    map_code_promotion_id.set(line.promotion_id, line.promotion_code)
                                }
                            })
                            if (promotions_code.length > 0) {
                                this.env.pos.removePromotionsApplied();
                                this.env.pos.applyPromotions(promotions);
                                promotions_code.forEach((promotion) => {
                                    this.env.pos.applyPromotionsCode(promotion, this.currentOrderder);
                                    let orderlines_after = this.currentOrder.orderlines;
                                    orderlines_after.forEach((line) => {
                                        if (line.promotion_id === promotion.id) {
                                            let code = map_code_promotion_id.get(line.promotion_id)
                                            line.setPromotionCode(code)
                                        }
                                    });
                                })
                                this.currentOrder.save_to_db();
                                this.generatePromotions();
                                this.generatePromotions_after_use_promotion();
                                if (this.check_promotion_type()) {
                                    await this.showPopup('ErrorPopup', {
                                        title: this.env._t('Thông báo'),
                                        body: this.env._t('Có ít nhất 2 chương trình khác loại được áp dụng trong đơn hàng.'),
                                    });
                                    return;
                                }
                                this.showScreen('PaymentScreen');
                                // đối với CTKM giảm giá hàng hóa theo giá trị đơn hàng thì phân bổ vào tất cả các SP trong đơn hàng
                                // this.allocate_promotion_total_amount()
                                this.allocate_total()
                            } else {
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
                                this.generatePromotions_after_use_promotion()
                                if (this.check_promotion_type()) {
                                    await this.showPopup('ErrorPopup', {
                                        title: this.env._t('Thông báo'),
                                        body: this.env._t('Có ít nhất 2 chương trình khác loại được áp dụng trong đơn hàng.'),
                                    });
                                    return;
                                }
                                this.showScreen('PaymentScreen');
                                // đối với CTKM giảm giá hàng hóa theo giá trị đơn hàng thì phân bổ vào tất cả các SP trong đơn hàng
                                // this.allocate_promotion_total_amount()
                                this.allocate_total()
                            }
                        } else if (applySelected) {
                            if (this.check_promotion_type()) {
                                await this.showPopup('ErrorPopup', {
                                    title: this.env._t('Thông báo'),
                                    body: this.env._t('Có ít nhất 2 chương trình khác loại được áp dụng trong đơn hàng.'),
                                });
                                return;
                            }
                            this.showScreen('PaymentScreen');
                            // đối với CTKM giảm giá hàng hóa theo giá trị đơn hàng thì phân bổ vào tất cả các SP trong đơn hàng
                            // this.allocate_promotion_total_amount()
                            this.allocate_total()
                        }
                    } else {
                        // super._onClickPay();
                        if (this.check_promotion_type()) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Thông báo'),
                                body: this.env._t('Có ít nhất 2 chương trình khác loại được áp dụng trong đơn hàng.'),
                            });
                            return;
                        }
                        this.showScreen('PaymentScreen');
                    }
                } else {
                    const orderlines = this.currentOrder.orderlines;
                    let promotions_code = []
                    const map_code_promotion_id = new Map()
                    // xóa giá phân bổ khi xóa CTKM
                    orderlines.forEach((line) => {
                        line.x_is_price_promotion = undefined
                        line.x_product_promotion = undefined
                    })
                    orderlines.forEach((line) => {
                        if (line.promotion_id && line.promotion_code) {
                            let promotion_after = self.posmodel.getPromotionById(line.promotion_id);
                            promotions_code.push(promotion_after)
                            map_code_promotion_id.set(line.promotion_id, line.promotion_code)
                        }
                    })
                    if (promotions_code.length > 0) {
                        this.env.pos.removePromotionsApplied();
                        this.env.pos.applyPromotions(promotions);
                        promotions_code.forEach((promotion) => {
                            this.env.pos.applyPromotionsCode(promotion, this.currentOrderder);
                            let orderlines_after = this.currentOrder.orderlines;
                            orderlines_after.forEach((line) => {
                                if (line.promotion_id === promotion.id) {
                                    let code = map_code_promotion_id.get(line.promotion_id)
                                    line.setPromotionCode(code)
                                }
                            });
                        })
                    }
                    if (promotions_code.length === 0) {
                        this.env.pos.removePromotionsApplied();
                        this.env.pos.applyPromotions(promotions);
                    }
                    this.generatePromotions();
                    this.generatePromotions_after_use_promotion()
                    if (this.check_promotion_type()) {
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Có ít nhất 2 chương trình khác loại được áp dụng trong đơn hàng.'),
                        });
                        return;
                    }
                    this.showScreen('PaymentScreen');
                    // đối với CTKM giảm giá hàng hóa theo giá trị đơn hàng thì phân bổ vào tất cả các SP trong đơn hàng
                    // this.allocate_promotion_total_amount()
                    this.allocate_total();
                }
                this.allocate_total();


            }

            check_promotion_type() {
                //{1} get all promotion applied to current order and promotion not allow applied with others
                //{2} remove all duplicate promotion type duplicate form that list
                //{3} return true if length of list unique type greater than 1
                var order = this.currentOrder;
                var order_line = order.get_orderlines();
                var promotion_applied = []
                for (let i = 0; i < order_line.length; i++) {
                    var line = order_line[i];
                    if (typeof line.promotion_id !== 'undefined') {
                        let promotion_line = self.posmodel.getPromotionById(line.promotion_id);

                        if (!promotion_applied.includes(line.promotion_id) && !promotion_line.x_allow_apply_with_other){
                            promotion_applied.push(promotion_line.promotion_type_id[0])
                        }
                    }
                }
                //get unique promotion id
                let unique_promotion_applied = [...new Set(promotion_applied)]
                return unique_promotion_applied.length > 1;
            }
        }

    Registries.Component.extend(ProductScreenCustom, ProductScreenPromotion);

    return ProductScreenCustom;
});
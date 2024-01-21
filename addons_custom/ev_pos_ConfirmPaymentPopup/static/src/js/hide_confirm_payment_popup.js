odoo.define('ev_pos_ConfirmPaymentPopup_custom.ProductScreenCustom', function (require) {
    "use strict"
    const core = require('web.core');
    // const ProductScreen = require('point_of_sale.ProductScreen');
    const ProductScreen = require('ev_pos_promotion.ProductScreen');
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
                                if(this.check_promotion_type()){
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
                                if(this.check_promotion_type()){
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
                            if(this.check_promotion_type()){
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
                        if(this.check_promotion_type()){
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
                    if(this.check_promotion_type()){
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

            check_promotion_type(){
                var promotions = this.env.pos.getValidPromotions(null, true);
                var order = this.currentOrder;
                var orderline = order.get_orderlines();
                var promotion_type = false;
                for(var i = 0; i < orderline.length; i++){
                    var line = orderline[i];
                    if(line.promotion_id != 'undefined'){
                        for(var j = 0; j < promotions.length; j++){
                            var promotion = promotions[j];
                            if(promotion.promotion_type_id == false){
                                continue;
                            }
                            if (promotion.id == line.promotion_id){
                                if(promotion_type == false){
                                   promotion_type = promotion.promotion_type_id[0]
                                } else {
                                    if(promotion_type != promotion.promotion_type_id[0]){
                                        return true;
                                    }
                                }
                            }
                        }
                    }
                }
                return false;
            }


        };

    Registries.Component.extend(ProductScreen, ProductScreenCustom);

    return ProductScreen;
});
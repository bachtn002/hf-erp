odoo.define('ev_pos_promotion.ProductScreen', function (require) {
    "use strict"

    const core = require('web.core');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const {useState} = owl.hooks;

    const _t = core._t;


    let PosPromotionProductScreen = ProductScreen =>
        class extends ProductScreen {

            /**
             * [Inheritant] constructor.
             */
            constructor() {
                super(...arguments);
                this.generatePromotions();
                this.handleOnClickClearPromotionButton = this.handleOnClickClearPromotionButton.bind(this);
                this.handleOnClickPromotionItem = this.handleOnClickPromotionItem.bind(this);
                this.handleOnClickSelect = this.handleOnClickSelect.bind(this);
                this.handleOnClickSelectAll = this.handleOnClickSelectAll.bind(this);
                // this.handleOnClickButtonPromotionVoucher = this.handleOnClickButtonPromotionVoucher.bind(this);
            }

            /**
             * [Inheritant] async r.
             *
             * Gọi hàm xoá dữ liệu promotions đã được áp dụng trước đó
             * Gọi hàm để xây dựng dữ liệu promotions phù hợp đơn hàng
             *
             * @param {} event
             */
            async _clickProduct(event) {
                super._clickProduct(event);
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }

            /**
             * [Inheritant] async _updateSelectedOrderline.
             *
             * Gọi hàm xoá dữ liệu promotions đã được áp dụng trước đó
             * Gọi hàm để xây dựng dữ liệu promotions phù hợp đơn hàng
             *
             * @param {} event
             */
            async _updateSelectedOrderline(event) {
                super._updateSelectedOrderline(event);
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }


            async _barcodeProductAction(code) {
                super._barcodeProductAction(code);
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }

            /**
             * gọi hàm để áp dụng CTKM với đối tượng KH
             * @returns {Promise<void>}
             * @private
             */
            async _onClickCustomer() {
                // IMPROVEMENT: This code snippet is very similar to selectClient of PaymentScreen.
                const currentClient = this.currentOrder.get_client();
                const {confirmed, payload: newClient} = await this.showTempScreen(
                    'ClientListScreen',
                    {client: currentClient}
                );
                if (confirmed) {
                    this.currentOrder.set_client(newClient);
                    this.currentOrder.updatePricelist(newClient);
                    this.env.pos.removePromotionsApplied();
                    this.generatePromotions();
                }
            }

            /**
             * []Inheritant _onClickPay.
             *
             * Hiển thị popup xác nhận áp dụng promotion
             *
             */
            async _onClickPay() {
                let promotions = this.env.pos.getValidPromotions(null, true);
                if (promotions.length > 0) {
                    let props = {
                        title: _t('Confirm payment'),
                        body: _t('Apply all promotions or selected promotion'),
                        confirmText: ('Apply all'),
                        cancelText: ('Cancel')
                    };
                    const {applyAll, applySelected} =
                        await this.showPopup('ConfirmPaymentPopup', props);
                    if (applyAll) {
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

            /**
             * generatePromotions.
             *
             * Đánh dấu promotion được chọn và cập nhật lại state
             *
             */
            generatePromotions() {
                // Lấy toàn bộ promotions đủ điều kiện áp dụng cho đơn hàng
                // let promotions = this.env.pos.getValidPromotions(null, true);
                // sửa lại
                let promotions_all = this.env.pos.getValidPromotions(null, true);
                let promotions = [];
                promotions_all.forEach((pro) => {
                    if (!pro.check_promotion) {
                        promotions.push(pro)
                    }
                })
                // Lấy toàn bộ promotions đã được áp dụng vào đơn hàng
                let appliedPromotions = this.env.pos.getPromotionsApplied();
                let appliedProIds = appliedPromotions.map((item) => {
                    return item.id;
                });
                // Cập nhật lại danh sách promotions với các promtion đã được chọn
                promotions.forEach((item) => {
                    let select = _.indexOf(appliedProIds, item.id) != -1;
                    item.setSelect(select);
                });
                this.state.promotions = promotions;
            }

            /**
             * handleOnClickClearPromotionButton.
             *
             * Hàm sử lý khi click vào nút clear promotions
             *
             * + Xoá toàn bộ promotions đã được áp dụng
             * + Gọi hàm xây dựng lại list promotions hiển thị trên view
             *
             * @param {} ev
             */
            handleOnClickClearPromotionButton(ev) {
                // Xoá toàn bộ promotions đã được áp dụng
                this.env.pos.removePromotionsApplied();
                // Xây dựng lại promotions hiển thị trên view
                this.generatePromotions();
            }

            /**
             * handleOnClickPromotionItem.
             *
             * Hàm sử lý khi click vào promotion item
             *
             * + Đánh dấu lại trạng thái promotion
             * + Sử lý áp dụng promotion cho đơn hàng
             *
             * @param {} ev
             * @param {} data
             */
            handleOnClickPromotionItem(ev, promotion) {
                ev.preventDefault();
                // Đánh dấu lại promotion được chọn
                this.state.appliedPromotions.forEach((item) => {
                    if (item.id === promotion.id) {
                        item.toggleSelect();
                    }
                });
                if (promotion.selected) {
                    // Nếu promotion được đánh dấu là chọn thì sẽ áp dụng vào đơn hàng
                    this.env.pos.applyPromotion(promotion);
                } else {
                    // Nếu promotion ko/huỷ đánh dấu thì huỷ áp dụng
                    this.env.pos.removePromotionApplied(promotion);
                }
                // Xây dựng lại dữ liệu promotion để hiển thị
                this.generatePromotions();
            }

            /**
             * handleOnClickSelect.
             *
             * Sử lý khi có sự kiện click nút Select trên PromotionPopup
             *
             * ${1} Cập nhật lại toàn bộ trạng thái của promotions trong state
             * ${2} Xoá toàn bộ promotion đã áp dụng
             * ${3} Áp dụng lại list promotion được chọn
             * ${3} Xây dựng lại view
             *
             * @param {} ev
             * @param {} promotions
             */
            handleOnClickSelect(ev, promotions) {
                let appliedPromotions = [];
                // ${1}
                let selectedPromIds = promotions.map((item) => {
                    return item.id;
                });
                this.state.promotions.forEach((item) => {
                    let select = _.indexOf(selectedPromIds, item.id) != -1;
                    item.setSelect(select);
                    if (item.selected)
                        appliedPromotions.push(item);
                });
                // ${2}
                this.env.pos.removePromotionsApplied();
                // ${3}
                this.env.pos.applyPromotions(appliedPromotions);
                // ${4}
                this.generatePromotions();
            }

            /**
             * handleOnClickSelectAll.
             *
             * Sử lý khi có sự kiện click nút SelectAll trên PromotionPopup
             *
             * ${1} Cập nhật lại toàn bộ trạng thái của promotions trong state
             * ${2} Xoá toàn bộ promotion đã áp dụng
             * ${3} Áp dụng lại list promotion được chọn
             * ${3} Xây dựng lại view
             *
             * @param {} ev
             * @param {} promotions
             */
            handleOnClickSelectAll(ev, promotions) {
                // ${1}
                this.state.promotions.forEach((item) => {
                    item.setSelect(true);
                });
                // ${2}
                this.env.pos.removePromotionsApplied();
                // ${3}
                this.env.pos.applyPromotions(promotions);
                // ${4}
                this.generatePromotions();
            }

        };

    Registries.Component.extend(ProductScreen, PosPromotionProductScreen);

    return ProductScreen;

});

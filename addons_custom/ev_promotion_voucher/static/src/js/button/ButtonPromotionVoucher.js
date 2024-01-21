odoo.define('ev_promotion_voucher.ButtonPromotionVoucher', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const PosDB = require('point_of_sale.DB');
    const models = require('ev_pos_promotion.Promotion');
    const Promotion = models.Promotion;
    var models_GiftTotalAmount = require('ev_pos_promotion_gift_total_amount.Promotion');
    const PromotionGiftTotal = models_GiftTotalAmount.Promotion;
    var models_pro = require('ev_pos_promotion.PosModel');
    const rpc = require('web.rpc');
    // lấy chương trình khuyến mại trong local storage
    PosDB.include({
        getDataPro: function (check_promotion) {
            let rows = this.load(check_promotion, []);
            return rows;
        },
    });

    class ButtonPromotionVoucher extends PosComponent {
        constructor() {
            super(...arguments);
            this.db = new PosDB;
            //CaoNV
            this.handleOnClickApplyPromotionCode = this.handleOnClickApplyPromotionCode.bind(this);
            //End CaoNV
        }

        handleOnClickApplyPromotionCode(ev, promotions) {
            this.props.onClickApplyPromotionCodeChade(ev, promotions);
        }


        get currentOrder() {
            return this.env.pos.get_order();
        }

        async onClickPromotionCode(ev) {
            ev.preventDefault();
            const order = this.currentOrder;
            let props = {
                title: this.env._t('Nhập mã CTKM!'),
                onClickApplyPromotionCodeCha: this.handleOnClickApplyPromotionCode,
                order: order,
            };
            this.showPopup('VoucherPromotionPopup', props);
            const {
                confirmed,
                payload,
                check_promotion,
                get_promotion_id,
                code_promotion
            } = await this.showPopup("VoucherPromotionPopup", props)
            if (confirmed) {
                let data_promotions_test = this.db.getDataPro(check_promotion);
                let data_promotions = this.db.load('promotions');
                if (data_promotions.length === 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Lỗi'),
                        body: this.env._t('Mã khuyến mại ko nằm trong chương trình khuyến mại áp dụng tại cửa hàng'),
                    });
                }
                data_promotions.forEach((data_promotion) => {
                        if (data_promotion.id === get_promotion_id && data_promotion.check_promotion === true) {
                            //xử lý hiện CTKM
                            let promotion_id = data_promotion.id
                            let promotion = self.posmodel.getPromotionById(promotion_id);
                            // áp dụng chương trình khuyến mại

                            let promotion_after = self.posmodel.getPromotionById(promotion_id);
                            if (!promotion_after.isValidOrder(order)) {
                                return
                            }
                            let check = false
                            order.orderlines.forEach((line) => {
                                if (line.promotion_id === promotion_id) {
                                    check = true
                                }
                            });
                            if (!check) {
                                // áp dụng mã CTKM vào đơn hàng
                                this.env.pos.applyPromotionsCode(promotion_after, order);

                                // gọi hàm cập nhật lại dòng KM ở ngay dưới SP được KM 😀😀
                                // promotion_after.applyPromotionToOrder(order);
                                order.orderlines.forEach((line) => {
                                    if (line.promotion_id === promotion_id) {
                                        line.setPromotionCode(code_promotion)
                                    }
                                });
                                //lưu promotion code đến order dưới trình duyệt
                                order.save_to_db();
                                //insert promotion vào bảng promotion_voucher_count
                                // let args_code = [order.name, order.name, code_promotion];
                                // this.rpc({
                                //     model: 'promotion.voucher.count',
                                //     method: 'update_promotion_used',
                                //     args: args_code,
                                // });
                            }
                            if (check) {
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('Lỗi'),
                                    body: this.env._t('Unable use more 2 promotion code on 1 CTKM'),
                                });
                                return
                            }


                        }
                    },
                    // this.props.onClickButtonVoucher()
                )
            } else {

                return
            }
        }

        async onClickButtonPromotionVoucher(event) {
            const order = this.currentOrder;
            const {
                confirmed,
                payload,
                check_promotion,
                get_promotion_id,
                code_promotion
            } = await this.showPopup("VoucherPromotionPopup", {
                title: this.env._t('Please type promotion code!'),
                order: order,
            });
            // thực hiện thêm chương trình khuyến mại
            if (confirmed) {
                let data_promotions_test = this.db.getDataPro(check_promotion);
                let data_promotions = this.db.load('promotions');

                if (data_promotions.length === 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Promotion code not appiled at shop'),
                    });
                }
                data_promotions.forEach((data_promotion) => {
                        if (data_promotion.id === get_promotion_id && data_promotion.check_promotion === true) {
                            //xử lý hiện CTKM
                            let promotion_id = data_promotion.id
                            let promotion = self.posmodel.getPromotionById(promotion_id);
                            // áp dụng chương trình khuyến mại

                            let promotion_after = self.posmodel.getPromotionById(promotion_id);
                            if (!promotion_after.isValidOrder(order)) {
                                return
                            }
                            // áp dụng mã CTKM vào đơn hàng
                            this.env.pos.applyPromotions(promotion_after);
                            order.orderlines.forEach((line) => {
                                if (line.promotion_id === promotion_id) {
                                    line.setPromotionCode(code_promotion)
                                }
                            });
                            //cập nhật số lần sử dụng mã
                            // let args = [promotion_id, code_promotion];
                            //Không sử dụng hàm update_promotion_used để update code_promotion nữa

                            // this.rpc({
                            //     model: 'promotion.voucher.line',
                            //     method: 'update_promotion_used',
                            //     args: args,
                            // }, {
                            //     timeout: 3000,
                            //     shadow: true,
                            // });

                        }
                    },
                )
            } else {

                return
            }
        }
    }

    ButtonPromotionVoucher.template = 'ButtonPromotionVoucher';
    Registries.Component.add(ButtonPromotionVoucher);

    return ButtonPromotionVoucher

});


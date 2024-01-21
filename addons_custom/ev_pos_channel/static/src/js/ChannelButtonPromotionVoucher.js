odoo.define('ev_pos_channel.ChannelButtonPromotionVoucher', function (require) {
    'use strict'
    const ButtonPromotionVoucher = require('ev_promotion_voucher_custom.ButtonPromotionVoucher')
    const Registries = require('point_of_sale.Registries')

    let ChannelButtonPromotionVoucher = ButtonPromotionVoucher => class extends ButtonPromotionVoucher {
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
                confirmed, payload, check_promotion, get_promotion_id, code_promotion
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
                        let select_channel_value = document.getElementById('select-channel').value
                        if (data_promotion.pos_channel_ids.includes(parseInt(select_channel_value)) === false) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Thông báo'),
                                body: this.env._t('Mã code này không thể áp dụng trên kênh hiện tại.'),
                            });
                            return
                        }
                        //xử lý hiện CTKM
                        let promotion_id = data_promotion.id
                        let promotion = self.posmodel.getPromotionById(promotion_id);

                        // áp dụng chương trình khuyến mại

                        let promotion_after = self.posmodel.getPromotionById(promotion_id);
                        if (!promotion_after.isValidOrder(order)) {
                            return
                        }
                        let check = false
                        let is_valid_promotion_type = true;
                        order.orderlines.forEach((line) => {
                            if (typeof line.promotion_code !== 'undefined') {
                                let line_promotion = self.posmodel.getPromotionById(line.promotion_id);
                                if (promotion.x_promotion_code_type === line_promotion.x_promotion_code_type) {
                                    is_valid_promotion_type = false;
                                }
                            }
                            if (line.promotion_id === promotion_id) {
                                check = true;
                            }
                        });
                        //Chỉ áp dụng tối đa 2 code trên mỗi loại CT promotion code
                        if (!is_valid_promotion_type) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Max Code Allowed Error'),
                                body: this.env._t('Unable use more 2 promotion code per order'),
                            });
                            return
                        }
                        if (!check) {
                            // áp dụng mã CTKM vào đơn hàng
                            this.env.pos.applyPromotionsCode(promotion_after, order);

                            // gọi hàm cập nhật lại dòng KM ở ngay dưới SP được KM 😀😀
                            order.orderlines.forEach((line) => {
                                if (line.promotion_id === promotion_id) {
                                    line.setPromotionCode(code_promotion)
                                }
                            });
                            //lưu promotion code đến order dưới trình duyệt
                            order.save_to_db();
                        }
                        if (check) {
                            //Chỉ áp dụng được một code trên mỗi loại CT promotion code
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Lỗi'),
                                body: this.env._t('Unable use more 2 promotion code on 1 CTKM'),
                            });
                        }
                    }
                },)
            }
        }
    }

    Registries.Component.extend(ButtonPromotionVoucher, ChannelButtonPromotionVoucher)
    return ButtonPromotionVoucher
})
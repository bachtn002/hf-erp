odoo.define('ev_pos_promotion_loyalty_point.ProductScreenCustomer', function (require) {
    'use strict'

    const ProductScreenCustomer = require('ev_pos_search_customer.ProductScreenCustomer')
    const Registries = require('point_of_sale.Registries')


    let ButtonVerifyBarcode = ProductScreenCustomer => class extends ProductScreenCustomer {
        async _onClickVerifyBarcode(ev) {
             ev.preventDefault();
             let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
             })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            if (this.env.pos.get_order().sale_online) {
                if (this.env.pos.get_order().is_created_by_api) {
                    return
                } else if (is_not_allow_editing) {
                    return
                }
            }
            const order = this.currentOrder;
            let props = {
                title: this.env._t('Nhập mã thành viên!'),
                onClickApplyPromotionCodeCha: this.handleOnClickApplyPromotionCode,
                order: order,
                isVerifyBarcode: true,
            };
            this.showPopup('VoucherPromotionPopup', props);

            const {
                confirmed
            } = await this.showPopup("VoucherPromotionPopup", props)

            if (confirmed) {
                this.props.upDatePromotion(ev);
            }
         }
    }


    Registries.Component.extend(ProductScreenCustomer, ButtonVerifyBarcode)
    return ButtonVerifyBarcode
})
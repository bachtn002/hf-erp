odoo.define('ev_pos_channel.ChannelPayment', function (require) {
    'use strict'

    const core = require('web.core');
    const ProductScreen = require('ev_promotion_voucher_custom.ProductScreenCustom')
    const Registries = require('point_of_sale.Registries')
    const {useListener} = require('web.custom_hooks')
    const _t = core._t

    let ChannelPayment = ProductScreen => class extends ProductScreen {

        constructor() {
            super(...arguments)
            this.generatePromotions()
            this.generatePromotionsByChannel()
            useListener('change-select-channel', this._onChangeSelectedChannel);
        }

        async _onClickPay() {
            this.env.pos.list_payment_methods_by_channel = []
            let select_channel_value = document.getElementById('select-channel').value
            this.env.pos.get_order().x_id_pos_channel = select_channel_value
            let payment = this.env.pos.payment_methods
            for (let i = 0; i < payment.length; i++) {
                if (payment[i]['pos_channel_ids'].includes(parseInt(select_channel_value)) === true) {
                    await this.env.pos.list_payment_methods_by_channel.push(payment[i])
                }
            }
            if (select_channel_value === '0') {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Thông báo'), body: this.env._t('Vui lòng chọn kênh bán hàng để thanh toán'),
                });
                return
            } else {
                super._onClickPay()
            }
        }

        _onChangeSelectedChannel() {
            self.posmodel.removePromotionsApplied(null)
            this.env.pos.get_order().x_select_channel_value = parseInt(document.getElementById('select-channel').value)
            this.generatePromotionsByChannel()
        }

        generatePromotionsByChannel() {
            console.log('chạy vào khởi tạo ctkm theo kênh...........')
            this.generatePromotions()
            let promotions_all = this.env.pos.getValidPromotions(null, true)
            console.log(promotions_all)
            let promotions = []
            promotions_all.forEach((pro) => {
                if (!pro.check_promotion) {
                    promotions.push(pro)
                }
            })
            let appliedPromotions = this.env.pos.getPromotionsApplied();
            let appliedProIds = appliedPromotions.map((item) => {
                return item.id
            });
            promotions.forEach((item) => {
                let select = _.indexOf(appliedProIds, item.id) != -1
                item.setSelect(select)
            })
            this.state.promotions = promotions
        }
    }

    Registries.Component.extend(ProductScreen, ChannelPayment)

    return ProductScreen
})
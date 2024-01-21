odoo.define('ev_pos_channel.ChannelConfirmPaymentPopup', function (require) {
    'use strict'
    const core = require('web.core')
    const AbstractAwaitablePopup = require('ev_pos_promotion.ConfirmPaymentPopup')
    const Registries = require('point_of_sale.Registries')
    let _t = core._t;

    let ChannelConfirmPaymentPopup = AbstractAwaitablePopup => class extends AbstractAwaitablePopup {
        async onClickApplySelected() {
            var list_promotion_apply = self.posmodel.getPromotionsApplied()
            let select_channel_value = document.getElementById('select-channel').value
            var check = true
            for (let i = 0; i < list_promotion_apply.length; i++) {
                if (list_promotion_apply[i].pos_channel_ids.includes(parseInt(select_channel_value)) === false) {
                    check = false
                    break
                }
            }
            if (check === false) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Thông báo'),
                    body: this.env._t('Có chương trình khuyến mại không thể áp dụng trên kênh hiện tại.'),
                });
                return
            }
            super.onClickApplySelected()
        }

        async onClickApplyAll() {
            var list_promotion_apply = self.posmodel.getValidPromotions()
            let select_channel_value = document.getElementById('select-channel').value
            var check = true
            for (let i = 0; i < list_promotion_apply.length; i++) {
                if (list_promotion_apply[i].pos_channel_ids.includes(parseInt(select_channel_value)) === false) {
                    check = false
                    break
                }
            }
            if (check === false) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Thông báo'),
                    body: this.env._t('Có chương trình khuyến mại không thể áp dụng trên kênh hiện tại.'),
                });
                return
            }
            super.onClickApplyAll()
        }
    }
    Registries.Component.extend(AbstractAwaitablePopup, ChannelConfirmPaymentPopup)

    return AbstractAwaitablePopup
})
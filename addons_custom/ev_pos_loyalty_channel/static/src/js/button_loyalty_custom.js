odoo.define('ev_pos_loyalty_channel.ButtonLoyaltyCustom', function (require) {
    "use strict"

    const ButtonLoyaltyCustom = require('ev_pos_loyalty_custom.ButtonLoyaltyCustom');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');

    const ChannelButtonLoyaltyCustom = ButtonLoyaltyCustom =>
        class extends ButtonLoyaltyCustom {
            async onClickButtonLoyaltyCustom(event) {
                let channel_ids = this.currentOrder.pos.loyalty.x_pos_channel_ids;
                let select_channel = document.getElementById('select-channel')
                var select_channel_value = parseInt(select_channel.value);
                if (select_channel_value === 0){
                    this.showPopup('ErrorPopup', {
                            title: this.env._t('Lỗi'),
                            body: this.env._t('Vui lòng chọn kênh bán hàng để sử dụng điểm'),
                        });
                    return
                }
                if (!channel_ids.includes(select_channel_value)){
                    this.showPopup('ErrorPopup', {
                            title: this.env._t('Lỗi'),
                            body: this.env._t('Không thể áp dụng Điểm thưởng trong kênh hiện tại'),
                        });
                    return
                }
                const result = await super.onClickButtonLoyaltyCustom(event);

                return result;
            }
    };

    Registries.Component.extend(ButtonLoyaltyCustom, ChannelButtonLoyaltyCustom);

    return ButtonLoyaltyCustom;
});


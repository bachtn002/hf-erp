odoo.define('ev_pos_promotion_loyalty_point.ButtonLoyaltyCustom', function (require) {
    "use strict"

    const ButtonLoyaltyCustom = require('ev_pos_loyalty_channel.ButtonLoyaltyCustom');
    const Registries = require('point_of_sale.Registries');

    const PromotionButtonLoyaltyCustom = ButtonLoyaltyCustom =>
        class extends ButtonLoyaltyCustom {
            async onClickButtonLoyaltyCustom(event) {
                const result = await super.onClickButtonLoyaltyCustom(event);
                if (this.currentOrder.get_spent_points() > 0 && this.currentOrder.get_points_promotion_loyalty() > 0) {
                    // Dùng điểm thưởng Nếu tiền sau khi sử dụng điểm không đủ áp dung CTKM
                    // tích lũy thành viên => cộng điểm lại
                    var list_promotion_apply = self.posmodel.getValidPromotions();
                    if(list_promotion_apply.length > 0) {
                        let promotionLoyalty_can_apply = list_promotion_apply.filter((item) => {
                            return item.type === 'loyalty_point';
                        });
                        promotionLoyalty_can_apply.forEach((p) => {
                            p.applyPromotionToOrder(this.currentOrder)
                        })
                    }else{
                         this.currentOrder.set_x_promotion_loyalty_point(0);
                    }

                }
                return result;
            }
        };

    Registries.Component.extend(ButtonLoyaltyCustom, PromotionButtonLoyaltyCustom);

    return ButtonLoyaltyCustom;
});
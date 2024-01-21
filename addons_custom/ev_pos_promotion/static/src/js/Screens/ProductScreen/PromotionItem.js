odoo.define('ev_pos_promotion.PromotionItem', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');


    class PromotionItem extends PosComponent {

        /**
         * onClickPromotionItem.
         *
         * Hàm sử lý dự kiện khi được click.
         * Gọi callback function thông qua props onClickPromotionItem
         *
         * @param {} ev Event onClick
         */
        onClickPromotionItem(ev) {
            ev.preventDefault();
            this.props.onClickPromotionItem(ev, this.props.promotion);
        }

    }

    PromotionItem.template = 'PromotionItem';

    Registries.Component.add(PromotionItem);

    return PromotionItem;

})

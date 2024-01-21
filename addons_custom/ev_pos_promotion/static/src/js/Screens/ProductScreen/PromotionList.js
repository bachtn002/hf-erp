odoo.define('ev_pos_promotion.PromotionList', function (require) {

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');


    class PromotionList extends PosComponent {

        /**
         * [Inheritant] constructor.
         *
         * Binding function handleOnClickPromotionItem
         *
         */
        constructor() {
            super(...arguments);

            this.handleOnClickPromotionItem = this.handleOnClickPromotionItem.bind(this);
        }

        /**
         * handleOnClickPromotionItem.
         *
         * Sử lý sự kiện khi click vào promotion item.
         *
         * Gọi callback thông qua props onClickPromotionItem
         *
         * @param {} ev
         * @param {} data
         */
        handleOnClickPromotionItem(ev, promotion) {
            this.props.onClickPromotionItem(ev, promotion);
        }

    }

    PromotionList.template = 'PromotionList';

    Registries.Component.add(PromotionList);

    return PromotionList;

});

odoo.define('ev_pos_promotion.PromotionContainer', function (require) {

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    const {useState} = owl.hooks;


    class PromotionContainer extends PosComponent {

        /**
         * [Inheritant] constructor.
         *
         * Quản lý state {title: ''}
         *
         * Binding handleOnClickPromotionItem
         *
         */
        constructor() {
            super(...arguments);
            this.state = useState({
                title: this.props.title || 'Promotions',
            });
        }

        /**
         * show.
         *
         * Kiểm tra có hiện thị container hay không dựa vào dữ liệu của
         * promotions.
         * true Nếu có dữ liệu
         * false Nếu không có dữ liệu
         *
         * @return bool: true/false
         *
         */
        get show() {
            return this.props.promotions && this.props.promotions.length > 0;
        }
        /**
         * handleOnClickPromotionItem.
         *
         * Sử lý sự kiện click vào promotion item,
         *
         * Gọi callback thông qua props onClickPromotionItem
         *
         * @param {} ev
         * @param {} data
         */
        handleOnClickPromotionItem(ev, promotion) {
            if (!this.props.onClickPromotionItem)
                return;
            this.props.onClickPromotionItem(ev, promotion);
        }
    }

    PromotionContainer.template = 'PromotionContainer';

    Registries.Component.add(PromotionContainer);

    return PromotionContainer;

});

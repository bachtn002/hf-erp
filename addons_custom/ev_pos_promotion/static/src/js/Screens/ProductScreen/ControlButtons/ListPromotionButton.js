odoo.define('ev_pos_promotion.ListPromotionButton', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class ListPromotionButton extends PosComponent {

        /**
         * constructor.
         *
         * Sử dụng để binding các action
         *
         */
        constructor() {
            super(...arguments);
            this.handleOnClickPromotionItem = this.handleOnClickPromotionItem.bind(this);
            this.handleOnClickSelect = this.handleOnClickSelect.bind(this);
            this.handleOnClickSelectAll = this.handleOnClickSelectAll.bind(this);
        }

        /**
         * handleOnClickPromotionItem.
         *
         * Hàm dùng để sử lý khi có sư kiện click vào promotion item
         * trên PromotionPopup. Hàm sẽ gọi callback thông qua
         * props onClickPromotionItem
         *
         * @param {} ev: Event onClick
         * @param {} promotion Json: chương trình khuyến mãi được click
         */
        handleOnClickPromotionItem(ev, promotion) {
            this.props.onClickPromotionItem(ev, promotion);
        }

        /**
         * handleOnClickSelect.
         *
         * Hàm dùng để sử lý sự kiện click select button trên PromotionPopup, hàm
         * sẽ gọi lại callback thông qua props onClickSelect
         *
         * @param {} ev Event onClick
         * @param [] promotions Array: Danh sách các promotion được chọn
         */
        handleOnClickSelect(ev, promotions) {
            this.props.onClickSelect(ev, promotions);
        }
        /**
         * handleOnClickSelectAll.
         *
         * Hàm dùng để sử lý sự kiện click select all button trên PromotionPopup,
         * hàm sẽ gọi lại callback thông qua props onClickSelectAll
         *
         * @param {} ev Event onClick
         * @param [] promotions Array: Danh sách các promotions được chọn
         */
        handleOnClickSelectAll(ev, promotions) {
            this.props.onClickSelectAll(ev, promotions)
        }

        /**
         * onClickListPromotionButton.
         *
         * Hàm dùng để sử lý sự kiện onClick trên button ListPromotionButton
         *
         * Show PromotionPopup với các props
         *
         * @param {} ev Event onClick
         */
        onClickListPromotionButton(ev) {
            ev.preventDefault();
            let props = {
                onClickPromotionItem: this.handleOnClickPromotionItem,
                onClickSelect: this.handleOnClickSelect,
                onClickSelectAll: this.handleOnClickSelectAll
            };
            this.showPopup('PromotionPopup', props);
        }
    }

    ListPromotionButton.template = 'ListPromotionButton'

    Registries.Component.add(ListPromotionButton)

    return ListPromotionButton

});

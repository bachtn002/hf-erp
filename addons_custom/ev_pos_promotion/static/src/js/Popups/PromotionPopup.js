odoo.define('ev_pos_promotion.PromotionPopup', function (require) {
    "use strict"

    const core = require('web.core');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    const {useState} = owl.hooks;
    const _t = core._t;


    class PromotionPopup extends AbstractAwaitablePopup {
        /**
         * constructor.
         *
         * Thêm promotions vào state
         * binding funtion handleOnClickPromotionItem
         *
         */
        constructor() {
            super(...arguments);
            // Lấy toàn bộ promotions đủ điều kiện áp dụng cho đơn hàng
            let promotions_all = this.env.pos.getValidPromotions(null, true);
            // Lấy toàn bộ promotions đã được áp dụng vào đơn hàng
            let appliedPromotions = this.env.pos.getPromotionsApplied();
            // Chuyển đổi danh sách promotions đã đươcj chọn về dạng list ids
            let appliedProIds = appliedPromotions.map((item) => {
                return item.id;
            });



            let promotions = [];
                promotions_all.forEach((pro) => {
                    if (!pro.check_promotion) {
                        promotions.push(pro)
                    }
                })

            // Cập nhật lại danh sách promotions với các promtion đã được chọn
            promotions.forEach((item) => {
                let select = _.indexOf(appliedProIds, item.id) != -1;
                item.setSelect(select);
            });

            this.state = useState({
                promotions: promotions,
                selectedPromotions: [],
            });
            this.handleOnClickPromotionItem = this.handleOnClickPromotionItem.bind(this);
        }

        /**
         * handleOnClickPromotionItem.
         *
         * Hàm sử lý khi click vào promotion item trên popup
         *
         *
         * @param {} ev: Event onClick
         * @param {} promotion
         */
        handleOnClickPromotionItem(ev, promotion) {


            ev.preventDefault();
            // Kiểm tra promotion đã đựoc chọn trước đó chưa
            let selectedPromotionsIds = this.state.selectedPromotions.map((item) => {
                return item.id;
            });
            let indexPromotion = _.indexOf(selectedPromotionsIds, promotion.id);
            if (indexPromotion != -1) {
                // Đã chọn => xoá
                this.state.selectedPromotions =
                    this.state.selectedPromotions.filter((v, i) => {
                        return i != indexPromotion;
                    })
                selectedPromotionsIds = selectedPromotionsIds.filter((id) => {
                    return id != promotion.id;
                });
            } else {
                // Chưa chọn => thêm => check qua các rule nếu có
                let selectedPromotions = this.state.selectedPromotions;
                selectedPromotions.push(promotion);
                selectedPromotions = this.env.pos.sortPromotions(selectedPromotions);
                this.state.selectedPromotions = selectedPromotions;
                selectedPromotionsIds = selectedPromotions.map((item) => {
                    return item.id;
                })
            }
            // Đánh dấu lại dữ liệu
            let copyPromotions = this.state.promotions;
            copyPromotions.forEach((item) => {
                let select = _.indexOf(selectedPromotionsIds, item.id) != -1;
                item.setSelect(select);
            });

            this.state.promotions = copyPromotions;
        }

        /**
         * onClickSelect.
         *
         * Hàm sử lý khi click vào nút select trên popup
         *
         * Hàm sẽ lọc các dữ liệu promotions đã được chọn trong list promotions
         * sau đó gửi lại parent thông qua callback onClickSelect
         *
         * @param {} ev: Event onClick
         */
        onClickSelect(ev) {
            ev.preventDefault();
            let checkedPromotions = this.state.promotions.filter((item) => {
                return item.selected;
            })
            this.props.onClickSelect(ev, checkedPromotions);
            this.cancel();
        }
        /**
         * onClickSelectAll.
         *
         * Hàm sử lý khi click vào nút selectAll trên popup
         *
         * Hàm sẽ gửi lại toàn bộ dữ liệu promotion đang có trong state
         * thông qua callback onClickSelectAll
         *
         * @param {} ev: Event onClick
         */
        onClickSelectAll(ev) {

            ev.preventDefault();
            this.props.onClickSelectAll(ev, this.state.promotions);
            this.cancel();
        }
    }

    PromotionPopup.template = 'PromotionPopup';
    PromotionPopup.defaultProps = {
        selectAllText: _t('Select all'),
        selectOneText: _t('Select'),
        cancelText: _t('Cancel'),
        title: _t('Promotions')
    }

    Registries.Component.add(PromotionPopup);

    return PromotionPopup;

});

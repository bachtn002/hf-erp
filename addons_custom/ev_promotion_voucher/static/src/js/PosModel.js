odoo.define("ev_promotion_voucher.pos", function (require) {
    "use strict";

    var models = require("point_of_sale.models");
    var PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        setPromotionAllocateNone: function (order = null) {
            // Lấy các khuyến mãi đã áp dụng cho đơn hàng
            order = order || this.get_order();
            const orderlines = order.orderlines;
//            // xóa giá phân bổ khi xóa CTKM
            orderlines.forEach((line) => {
                line.x_is_price_promotion = undefined
                line.x_product_promotion = undefined
            })
            return [];
        },
    })
})
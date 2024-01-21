odoo.define('ev_pos_search_customer.SearchCustomerScreen', function (require) {
    "use strict"
    const core = require('web.core');
    // const ProductScreen = require('point_of_sale.ProductScreen');
    const ProductScreen = require('ev_promotion_voucher.PromotionVoucherProductScreen');
    const Registries = require('point_of_sale.Registries');

    const {useState} = owl.hooks;
    let SearchCustomerScreen = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                this.generatePromotions();
                this.handleOnClickSearchCustomer = this.handleOnClickSearchCustomer.bind(this);
                this.upDatePromotion = this.upDatePromotion.bind(this);
            }

            //hàm cập nhật CTKM trên POS gọi callback tới pos_promotion
            handleOnClickSearchCustomer(ev, promotions) {
                console.log('test check onclick1')
            }

            upDatePromotion(ev, promotions) {
                this.env.pos.removePromotionsApplied();
                this.generatePromotions();
            }

            async _onClickCustomer() {
                const currentClient = this.currentOrder.get_client();
                if (currentClient != null) {
                    const {confirmed, payload: newClient} = await this.showTempScreen(
                        'ClientListScreen',
                        {client: currentClient}
                    );
                    if (confirmed) {
                        let order = this.env.pos.get_order();
                        // let promotion_code = []
                        // let promotion_id = []
                        // order.orderlines.forEach((line) => {
                        //     if (line.promotion_code && line.promotion_id) {
                        //         promotion_code.push(line.promotion_code)
                        //         promotion_id.push(line.promotion_id)
                        //         promotion_code.forEach((code) => {
                        //             let args_code = [order.name, order.name, code];
                        //             this.rpc({
                        //                 model: 'promotion.voucher.count',
                        //                 method: 'delete_promotion_code_used',
                        //                 args: args_code,
                        //             });
                        //         })
                        //     }
                        // });
                        this.currentOrder.set_client(newClient);
                        this.currentOrder.updatePricelist(newClient);
                        // bỏ chọn CTKM general lại màn POS
                        this.env.pos.removePromotionsApplied();
                        this.generatePromotions()
                    }
                }
            }

        };
    Registries.Component.extend(ProductScreen, SearchCustomerScreen);

    return ProductScreen;
});
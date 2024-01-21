odoo.define('ev_pos_voucher_ui.ProductScreenVoucher', function (require) {
    'use strict';

    const {useState} = owl.hooks;
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');


    let ProductScreenVoucher = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                this._id = 0;
            }

            async _updateSelectedOrderline(event) {
                await super._updateSelectedOrderline(event);
                // const order = this.currentOrder;
                // const orderlines = this.currentOrder.orderlines;
                // orderlines.forEach((line) => {
                //     if (line.has_product_lot) {
                //         order.remove_orderline(line);
                //     }
                // });

                let order = this.env.pos.get_order();
                let selectedLine = order.get_selected_orderline();
                if (selectedLine && selectedLine.has_product_lot) {
                    console.log('event.detail.buffer', event.detail.buffer)
                    if (event.detail.buffer > 1) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Lỗi'),
                            body: this.env._t('Không thể thay đổi số lượng voucher'),
                        });
                        this._setValue(1);
                        return;
                    }
                }
            }

            async _clickProduct(event) {
                const order = this.currentOrder;
                const orderlines = this.currentOrder.orderlines;
                // orderlines.forEach((line) => {
                //     if (line.has_product_lot) {
                //         order.remove_orderline(line);
                //     }
                // });
                const product = event.detail;
                if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
                    if (!this.currentOrder) {
                        this.env.pos.add_new_order();
                    }
                    const order = this.currentOrder;
                    let price_extra = 0.0;
                    let draftPackLotLines, weight, description, packLotLinesToEdit;
                    let lot_names = []
                    if (this.env.pos.config.product_configurator && _.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
                        let attributes = _.map(product.attribute_line_ids, (id) => this.env.pos.attributes_by_ptal_id[id])
                            .filter((attr) => attr !== undefined);
                        let {confirmed, payload} = await this.showPopup('ProductConfiguratorPopup', {
                            product: product,
                            attributes: attributes,
                        });

                        if (confirmed) {
                            description = payload.selected_attributes.join(', ');
                            price_extra += payload.price_extra;
                        } else {
                            return;
                        }
                    }

                    // Gather lot information if required.
                    if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
                        const isAllowOnlyOneLot = product.isAllowOnlyOneLot();
                        packLotLinesToEdit = [];
                        // if (isAllowOnlyOneLot) {
                        //     packLotLinesToEdit = [];
                        // } else {
                        //     const orderline = this.currentOrder
                        //         .get_orderlines()
                        //         .filter(line => !line.get_discount())
                        //         .find(line => line.product.id === product.id);
                        //     if (orderline) {
                        //         packLotLinesToEdit = orderline.getPackLotLinesToEdit();
                        //     } else {
                        //         packLotLinesToEdit = [];
                        //     }
                        // }
                        const {confirmed, payload} = await this.showPopup('EditListPopup', {
                            title: this.env._t('Vui lòng nhập mã phiếu mua hàng để bán!'),
                            isSingleItem: isAllowOnlyOneLot,
                            array: packLotLinesToEdit,
                            product: product,
                            order: order,
                        });
                        if (confirmed) {
                            // Segregate the old and new packlot lines
                            const modifiedPackLotLines = Object.fromEntries(
                                payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
                            );
                            const newPackLotLines = payload.newArray
                                .filter(item => !item.id)
                                .map(item => ({lot_name: item.text}));

                            draftPackLotLines = {modifiedPackLotLines, newPackLotLines};
                        } else {
                            // We don't proceed on adding product.
                            return;
                        }
                        const orderlines = this.currentOrder.orderlines;
                        if (orderlines) {
                            orderlines.forEach((line) => {
                                if (line.pack_lot_lines) {
                                    let line_lot_name = line.pack_lot_lines.models[0].changed.lot_name
                                    if (!lot_names.includes(line_lot_name)) {
                                        lot_names.push(line_lot_name);
                                    }
                                }
                            });
                        }
                    }

                    // Take the weight if necessary.
                    if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
                        // Show the ScaleScreen to weigh the product.
                        if (this.isScaleAvailable) {
                            const {confirmed, payload} = await this.showTempScreen('ScaleScreen', {
                                product,
                            });
                            if (confirmed) {
                                weight = payload.weight;
                            } else {
                                // do not add the product;
                                return;
                            }
                        } else {
                            await this._onScaleNotAvailable();
                        }
                    }
                    var check_merge = true;
                    if (draftPackLotLines) {
                        if (!lot_names.includes(draftPackLotLines.newPackLotLines[0].lot_name)) {
                            check_merge = false;
                        }
                    }
                    // Add the product after having the extra information.
                    this.currentOrder.add_product(product, {
                        draftPackLotLines,
                        description: description,
                        price_extra: price_extra,
                        quantity: weight,
                        merge: check_merge,
                    });
                    NumberBuffer.reset();
                } else {
                    super._clickProduct(event)
                }
            }

            async _onClickPay() {
                var self = this;
                var remove_payment = []
                const order = this.currentOrder;
                var paymentlines = order.paymentlines;
                paymentlines.forEach((line) => {
                    if (line.payment_method.x_is_voucher == true) {
                        remove_payment.push(line)
                    }
                });
                remove_payment.forEach((line) => {
                    order.remove_paymentline(line)
                });
                super._onClickPay();
            }

//            async _barcodeProductAction(code) {
////             NOTE: scan_product call has side effect in pos if it returned true.
//                if (!this.env.pos.scan_product(code)) {
//                    let array = []
//                    array.push({
//                        text: code.code,
//                        _id: 0
//                    })
//                    let payload = {newArray: array}
//                    const order = this.currentOrder;
//                    var customerID = false;
//                    var product = false
//                    if (order.get_client()) {
//                        customerID = order.get_client().id;
//                    }
//                    var message = undefined;
//                    let id = this._id
//                    let name = code.code
//                    let args = [id, name, customerID];
//                    var ifConnected = window.navigator.onLine;
//                    if (!ifConnected) {
//                        message = '* Đường truyền mạng có vấn đề. Vui lòng kiểm tra lại!';
//                    }
//                    const result = await this.rpc({
//                        model: 'stock.production.lot',
//                        method: 'check_code_from_ui',
//                        args: args,
//                    }).then((response) => {
//                        if ('message' in response) {
//                            message = '* ' + response['message'];
//                        } else {
//                            product = this.env.pos.db.get_product_by_id(response['product_id'])
//                            if (product == undefined) {
//                                message = '* Voucher/coupon chưa được cấu hình bán trên POS. Vui lòng kiểm tra lại!'
//                            } else {
//                                if (code.type === 'price') {
//                                    order.add_product(product, {price: code.value});
//                                } else if (code.type === 'weight') {
//                                    order.add_product(product, {quantity: code.value, merge: false});
//                                } else if (code.type === 'discount') {
//                                    order.add_product(product, {discount: code.value, merge: false});
//                                } else {
//                                    const order = this.currentOrder;
//                                    const orderlines = this.currentOrder.orderlines;
//                                    let price_extra = 0.0;
//                                    let draftPackLotLines, weight, description;
//                                    let lot_names = []
//                                    if (orderlines) {
//                                        orderlines.forEach((line) => {
//                                            if (line.pack_lot_lines) {
//                                                let line_lot_name = line.pack_lot_lines.models[0].changed.lot_name
//                                                if (!lot_names.includes(line_lot_name)) {
//                                                    lot_names.push(line_lot_name);
//                                                }
//                                            }
//                                        });
//                                    }
//                                    const modifiedPackLotLines = Object.fromEntries(
//                                        payload.newArray.filter(item => item.id).map(item => [item.id, item.text]));
//                                    const newPackLotLines = []
//                                    newPackLotLines.push({lot_name: code.code})
//                                    draftPackLotLines = {modifiedPackLotLines, newPackLotLines}
//                                    var check_merge = true;
//                                    if (draftPackLotLines) {
//                                        if (!lot_names.includes(draftPackLotLines.newPackLotLines[0].lot_name)) {
//                                            check_merge = false;
//                                        }
//                                    }
//                                    this.currentOrder.add_product(product, {
//                                        draftPackLotLines,
//                                        merge: check_merge,
//                                    });
//                                    NumberBuffer.reset();
//                                }
//                            }
//                        }
//                    });
//                    if (message != undefined) {
//                        this.showPopup('ErrorBarcodePopup', {
//                            code: this._codeRepr(code),
//                            message: message
//                        });
//                    }
//                }
//            }
        }
    Registries.Component.extend(ProductScreen, ProductScreenVoucher);

    return ProductScreen;
});

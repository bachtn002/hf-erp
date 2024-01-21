odoo.define("ev_google_maps.PaymentScreen", function (require) {
    "use strict";

    const core = require('web.core');
    const { Gui } = require('point_of_sale.Gui');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    var _t = core._t;

    let PaymentScreenSource = PaymentScreen =>
        class extends PaymentScreen {

             isNumeric(str) {
                 return /^\d+$/.test(str);
             }

            checkHomeDeliveryInfo(delivery_checked) {
                let check_error = []
                if (delivery_checked){
                    var x_address_delivery = $('#x_address_delivery')[0].innerText;
                    var x_cod = $('#x_cod')[0].value;
                    var x_lat = $('#x_lat')[0].innerText;
                    var x_long = $('#x_long')[0].innerText;
                    var x_partner_phone = $('#x_partner_phone')[0].value;
                    var x_receiver = $('#x_receiver')[0].value;
                    var order = this.currentOrder;

                    if (!order.get_client()){
                        check_error.push(_t("Vui lòng chọn khách hàng với đơn giao hàng tại nhà!"))
                        return check_error
                    }

                    if (!this.isNumeric(x_cod) && x_cod !== '') {
                        check_error.push("Tiền thu hộ không đúng định dạng số")
                        return check_error
                    }
                    if (x_address_delivery === "") {
                        check_error.push("Bạn chưa nhập địa chỉ giao hàng")
                        return check_error
                    }
                    if (x_lat === "") {
                        check_error.push("Vĩ độ giao hàng thiếu, vui lòng nhập lại địa chỉ giao hàng")
                        return check_error
                    }
                    if (x_long === "") {
                        check_error.push("Kinh độ giao hàng thiếu, vui lòng nhập lại địa chỉ giao hàng")
                        return check_error;
                    }

                    if (x_receiver === "") {
                        check_error.push("Thiếu thông tin Người nhận, vui lòng chọn lại khách hàng")
                        return check_error;
                    }

                    if (x_partner_phone === "") {
                        check_error.push("Thiếu thông tin Số điện thoại,  vui lòng chọn lại khách hàng")
                        return check_error;
                    }
                    return check_error
                }
            }

            updateHomeDeliveryVals(){
                var order = this.currentOrder;
                var x_home_delivery = $('#x_home_delivery')[0].checked;
                order.set_x_home_delivery(x_home_delivery);

                if (x_home_delivery){
                    var x_address_delivery = $('#x_address_delivery')[0].innerText;
                    var x_lat = $('#x_lat')[0].innerText;
                    var x_long = $('#x_long')[0].innerText;
                    var x_ship_note = $('#x_ship_note')[0].value;
                    var x_partner_phone = $('#x_partner_phone')[0].value;
                    var x_receiver = $('#x_receiver')[0].value;
                    var x_ship_type = $('#ship_type').val();
                    var x_cod = $('#x_cod')[0].value;
                    var x_distance = $('#x_ship_distance')[0].innerText;
                    order.set_x_cod(x_cod);
                    order.set_x_distance(x_distance);
                    order.set_x_address_delivery(x_address_delivery);
                    order.set_x_lat(x_lat);
                    order.set_x_long(x_long);
                    if (x_ship_type === '0') {
                        order.set_x_ship_type('internal')
                    } else {
                        order.set_x_ship_type('other')
                    }
                    order.set_x_receiver(x_receiver);
                    order.set_x_partner_phone(x_partner_phone);
                    order.set_x_ship_note(x_ship_note);
                }
            }

            async validateOrder(isForceValidate) {
                var x_home_delivery = $('#x_home_delivery')[0].checked;
                if (x_home_delivery) {
                    var message = this.checkHomeDeliveryInfo(true)
                    if (message.length > 0) {
                        Gui.showPopup('ErrorPopup', {
                            'title': _t('Thông báo'),
                            'body': _t(message),
                        });
                    } else {
                        this.updateHomeDeliveryVals();
                        super.validateOrder(isForceValidate);
                    }
                } else {
                    super.validateOrder(isForceValidate);
                }
            }

        }

    Registries.Component.extend(PaymentScreen, PaymentScreenSource);
    return PaymentScreen;
});
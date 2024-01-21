odoo.define('ev_payment_qrcode.PaymentScreen', function (require) {
    'use strict'
    const core = require('web.core')
    const _t = core._t
    const Registries = require('point_of_sale.Registries')
    const PaymentScreen = require('point_of_sale.PaymentScreen')
    const {useListener} = require('web.custom_hooks')
    const rpc = require('web.rpc')

    let PaymentScreenQRCode = PaymentScreen => class extends PaymentScreen {
        constructor(props) {
            super(...arguments)
        }

        addNewPaymentLine({detail: paymentMethod}) {
            let flag = false
            if (paymentMethod.is_qrcode_payment) {
                let payment_line_models = this.currentOrder.paymentlines.models
                payment_line_models.forEach((item) => {
                    if (item['payment_method']['id'] === paymentMethod['id']) {
                        flag = true
                        return
                    }
                })
            }
            if (!flag)
                super.addNewPaymentLine({detail: paymentMethod})
        }

        async validateOrder(isForceValidate) {
            let check_payment_method = false
            let amount_payment_qrcode = 0
            let payment_line_models = this.currentOrder.paymentlines.models
            payment_line_models.forEach((item) => {
                if (item.payment_method.is_qrcode_payment === true) {
                    check_payment_method = true
                    amount_payment_qrcode += parseFloat(item.amount)
                }
            })
            if (check_payment_method) {

                // Chặn click xác nhận đơn nhiều lần
                document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "none"

                let pos_session_id = this.currentOrder.pos_session_id
                let created_date_order = new Date(this.currentOrder.creation_date.toString())
                let number_created_date_order =
                    parseInt(created_date_order.getDate().toString() +
                        (created_date_order.getMonth() + 1).toString() +
                        created_date_order.getFullYear().toString())
                let created_date_session = new Date(this.currentOrder.pos.pos_session.start_at.toString())
                created_date_session.setHours(created_date_session.getHours() + 7)
                let number_created_date_session =
                    parseInt(created_date_session.getDate().toString() +
                        (created_date_session.getMonth() + 1).toString() +
                        created_date_session.getFullYear().toString())
                if (number_created_date_order !== number_created_date_session) {
                    document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Bạn không thể bán hàng của phiên ngày hôm trước!'),
                    })
                    return
                }
                // Clear interval expire time qrcode
                this.env.pos.current_interval.forEach((item) => {
                    clearInterval(item)
                })
                let pg_order_reference = this.env.pos.pg_order_reference
                this.env.pos.data_for_mbpay_paygate_detail = []
                // Call api get qrcode url
                let return_url = ''
                let current_order = this.currentOrder
                let order_reference = current_order['name'].toString().replaceAll('-', '')
                let amount = amount_payment_qrcode.toString()
                let access_code = ''
                let merchant_id = this.env.pos.merchant_id
                let mi_ss_now = new Date().toTimeString().slice(3, 8).replaceAll(':', '')
                let x_code_shop = this.env.pos['config']['x_code_shop']


                //Check log payment_qrcode_transaction
                let check_log = false
                let check_result_api_paygate_detail = false
                let flag = false
                var orderlines = this.currentOrder.get_orderlines();
                for (var i = 0; i < orderlines.length; i++) {
                    var line = orderlines[i];
                    if (line.quantity == 0) {
                        flag = true
                        document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                        await this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Trong đơn hàng có sản phẩm số lượng bằng 0. Hãy quay lại và xóa khỏi đơn hàng.'),
                        })
                        return
                    }
                }
                if (amount_payment_qrcode > 200000000 || amount_payment_qrcode < 2000) {
                    flag = true
                    document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Giá trị thanh toán QRCODE phải lớn hơn hai nghìn đồng và nhỏ hơn hai trăm triệu đồng'),
                    })
                    return
                }

                rpc.query({
                    model: 'payment.qrcode.transaction',
                    method: 'action_check_order_reference',
                    args: [null, order_reference, parseFloat(amount_payment_qrcode)]
                }, {
                    timeout: 2000
                })
                    .then((res) => {
                        console.log('action_check_order_reference validateOrder', res)
                        if (res) {
                            check_log = true
                        }
                    })
                    .catch((error) => {
                        flag = true
                        document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                        })
                        return
                    })
                if (check_log === false && current_order.check_create_qrcode_first_time === true) {
                    // Request API paygate detail
                    let today = new Date()
                    let pay_date = String(today.getDate()).padStart(2, '0')
                        + String(today.getMonth() + 1).padStart(2, '0')
                        + today.getFullYear()
                    let params = {
                        'mac_type': 'MD5',
                        'mac': '',
                        'merchant_id': merchant_id,
                        'order_reference': pg_order_reference,
                        'pay_date': pay_date
                    }
                    let inputMD5 = ''
                    let keys = Object.keys(params).sort()
                    for (let i in keys) {
                        if (params[keys[i]] && keys[i] !== 'mac_type' && keys[i] !== 'mac') {
                            if (params.hasOwnProperty(keys[i])) {
                                if (inputMD5 !== '') {
                                    inputMD5 += '&'
                                }
                                inputMD5 += keys[i] + '=' + params[keys[i]]
                            }
                        }
                    }
                    await rpc.query({
                        model: 'payment.qrcode.transaction',
                        method: 'action_api__mbpay_paygate_detail',
                        args: [null, params, inputMD5]
                    }, {
                        timeout: 2000
                    })
                        .then((result) => {
                            console.log('action_api__mbpay_paygate_detail validateOrder', result)
                            if ((result['error_code'] === '00' && result['amount'] === parseFloat(amount_payment_qrcode)) || result['error_code'] === '13') {
                                check_result_api_paygate_detail = true
                            }
                        })
                        .catch((error) => {
                            document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                            flag = true
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Thông báo'),
                                body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                            })
                            return
                        })
                } else {
                    check_result_api_paygate_detail = false
                }
                this.env.pos.pg_order_reference = 'T6QR' + order_reference + mi_ss_now
                if (check_log === false && check_result_api_paygate_detail === false && flag === false) {
                    this.showPopup('QRCodePopup')
                    this.env.pos.get_order().is_calling_qrcode_payment = true

                    let params = {
                        'access_code': access_code,
                        'amount': amount,
                        'cancel_url': null,
                        'currency': 'vnd',
                        'ipn_url': return_url,
                        'merchant_id': merchant_id,
                        'order_info': 'TT GIAO DICH ' + x_code_shop.toString(),
                        'order_reference': 'T6QR' + order_reference + mi_ss_now,
                        'pay_type': 'pay',
                        'payment_method': 'QR',
                        'return_url': null,
                        'mac_type': 'MD5',
                        'mac': '',
                    }

                    console.log('params_action_api__mbpay_create_order', params)
                    rpc.query({
                        model: 'payment.qrcode.transaction',
                        method: 'action_api__mbpay_create_order',
                        args: [null, params]
                    }, {
                        timeout: 4000
                    })
                        .then((result) => {
                            console.log(result)
                            if (!result) {
                                flag = true
                                document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                                this.env.pos.get_order().is_calling_qrcode_payment = false
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('Thông báo'),
                                    body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                                })
                                return
                            }
                            if (result['error_code'] !== '00') {
                                document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                                this.env.pos.get_order().is_calling_qrcode_payment = false
                                flag = true
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('Thông báo'),
                                    body: this.env._t(result['message']),
                                })
                                return
                            } else {
                                // Đánh dấu đã lấy qrcode thành công 1 lần
                                current_order.check_create_qrcode_first_time = true
                                // Save data for action_api__mbpay_paygate_detail
                                this.env.pos.data_for_mbpay_paygate_detail.push(
                                    [
                                        params['order_reference'],
                                        params['merchant_id'],
                                        (result['expire_time'].slice(3, 5) + result['expire_time'].slice(0, 2) + result['expire_time'].slice(6, 10)).toString(),
                                        result['session_id'],
                                        parseFloat(amount_payment_qrcode),
                                    ]
                                )
                                let payment_url = result['payment_url']
                                let order_reference = result['order_reference']
                                let amount = result['amount']
                                $('#url-mbpay-payment-gate').text(payment_url)
                                let qr_url = result['qr_url']
                                let qr_base64 = result['qr_base64']
                                let expire_time = Date.parse(result['expire_time'])

                                setTimeout(() => {
                                    $('#img-qrcode').css('display', 'inline-block')
                                    $('#img-qrcode').attr('src', 'data:image/png;base64, ' + qr_base64)
                                    $('#qrcode-button-confirm').css('background-color', '#007bff')
                                    $('#qrcode-button-confirm').css('pointer-events', 'auto')
                                    $('#qrcode-button-open').css('background-color', '#007bff')
                                    $('#qrcode-button-open').css('pointer-events', 'auto')

                                    let expired_time_qrcode_interval = setInterval(() => {
                                        let now = new Date().getTime()
                                        let remaining_time = expire_time - now
                                        let minutes = Math.floor((remaining_time % (1000 * 60 * 60)) / (1000 * 60))
                                        let seconds = Math.floor((remaining_time % (1000 * 60)) / 1000)
                                        $('#qrcode-expired-time').text(minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0'))

                                        if (remaining_time < 0) {
                                            clearInterval(expired_time_qrcode_interval)
                                            $('#img-danger-qrcode').css('display', 'inline-block')
                                            $('#img-qrcode').css('display', 'none')
                                            $('#qrcode-expired-time').text('')
                                            $('#qrcode-expired-time-main').text('Mã QR đã hết hạn thanh toán.')
                                            $('#qrcode-button-open').css('background-color', '#d4e9ff')
                                            $('#qrcode-button-open').css('pointer-events', 'none')
                                        }
                                    }, 1000)
                                    this.env.pos.current_interval.push(expired_time_qrcode_interval)
                                }, 1)
                            }
                        })
                        .catch((error) => {
                            flag = true
                            document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                            this.env.pos.get_order().is_calling_qrcode_payment = false
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Thông báo'),
                                body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                            })
                            return
                        })

                    const {result_api__mbpay_paygate_detail} = await this.showPopup('QRCodePopup')
                    if (result_api__mbpay_paygate_detail) {
                        document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                        this.env.pos.get_order().is_calling_qrcode_payment = false
                        super.validateOrder(isForceValidate)
                    }
                } else {
                    if (!flag) {
                        super.validateOrder(isForceValidate)
                    }
                }
            } else {
                super.validateOrder(isForceValidate)
            }
        }
    }

    Registries.Component.extend(PaymentScreen, PaymentScreenQRCode)
    return PaymentScreen
})
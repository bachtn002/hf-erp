odoo.define('ev_payment_qrcode.QRCodePopup', function (require) {
    "use strict"

    const core = require('web.core')
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup')
    const PaymentScreen = require('point_of_sale.PaymentScreen')
    const Registries = require('point_of_sale.Registries')
    const {useListener} = require('web.custom_hooks')
    const rpc = require('web.rpc')
    const NumberBuffer = require('point_of_sale.NumberBuffer')

    class QRCodePopup extends AbstractAwaitablePopup {
        constructor(props) {
            super(...arguments)
            useListener('click-qrcode-button-cancel', this._onClickCancelPaymentQRCode)
            useListener('click-qrcode-button-open', this._onClickOpenPaymentGate)
            useListener('click-qrcode-button-confirm', this._onClickConfirmPaygateDetail)
        }

        async _onClickCancelPaymentQRCode() {
            document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
            document.getElementById('qrcode-button-cancel').style.pointerEvents = "none"
            let interval___onClickCancelPaymentQRCode = setInterval(() => {
                $('#qrcode-button-cancel').css('pointer-events', 'all')
            }, 1000)
            this.env.pos.current_interval.forEach((item) => {
                clearInterval(item)
            })
            // Case nhấn xác nhận => Hiển thị popup => chưa gọi API thanh toán xong => nhấn hủy => chưa có giá trị payment từ MB
            if (this.env.pos.data_for_mbpay_paygate_detail.length === 0) {
                return
            }
            let order_reference = this.env.pos.data_for_mbpay_paygate_detail[0][0]
            console.log('order_reference _onClickCancelPaymentQRCode')
            let merchant_id = this.env.pos.data_for_mbpay_paygate_detail[0][1]
            let pay_date = this.env.pos.data_for_mbpay_paygate_detail[0][2]
            let amount = this.env.pos.data_for_mbpay_paygate_detail[0][4]
            let params = {
                'mac_type': 'MD5',
                'mac': '',
                'merchant_id': merchant_id,
                'order_reference': order_reference,
                'pay_date': pay_date
            }
            let keys = Object.keys(params).sort()
            let inputMD5 = ''
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

            // Flag for check record payment_qrcode_transaction
            var transaction_flag = true
            // Request check record payment_qrcode_transaction
            await rpc.query({
                model: 'payment.qrcode.transaction',
                method: 'action_check_order_reference',
                args: [null, order_reference.slice(4, -4), amount]
            }, {
                timeout: 2000
            })
                .then((result) => {
                    $('#qrcode-button-cancel').css('pointer-events', 'all')
                    console.log('RES _onClickCancelPaymentQRCode action_check_order_reference', result)
                    if (result) {
                        $('#message-error-qrcode').css('display', 'inline-block')
                        $('#message-error-qrcode').text('Đơn hàng đã được thanh toán. Vui lòng xác nhận đơn hàng.')
                        $('#qrcode-expired-time-main').css('display', 'none')
                        $('#img-danger-qrcode').css('display', 'inline-block')
                        $('#img-qrcode').css('display', 'none')
                    } else {
                        transaction_flag = false
                    }
                })
                .catch((error) => {
                    $('#qrcode-button-cancel').css('pointer-events', 'all')
                    document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                    this.env.pos.get_order().is_calling_qrcode_payment = false
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                    })
                    return
                })
            if (transaction_flag === false) {
                // Request API mbpay_paygate_detail
                rpc.query({
                    model: 'payment.qrcode.transaction',
                    method: 'action_api__mbpay_paygate_detail',
                    args: [null, params, inputMD5]
                }, {
                    timeout: 2000
                })
                    .then((result) => {
                        $('#qrcode-button-cancel').css('pointer-events', 'all')
                        console.log('RES _onClickCancelPaymentQRCode action_api__mbpay_paygate_detail', result)
                        if ((result['error_code'] === '00' && parseFloat(result['amount']) === amount) || result['error_code'] === '13') {
                            $('#message-error-qrcode').css('display', 'inline-block')
                            $('#message-error-qrcode').text('Đơn hàng đã được thanh toán. Vui lòng xác nhận đơn hàng.')
                            $('#qrcode-expired-time-main').css('display', 'none')
                            $('#img-danger-qrcode').css('display', 'inline-block')
                            $('#img-qrcode').css('display', 'none')
                        } else {
                            this.env.pos.get_order().is_calling_qrcode_payment = false
                            this.trigger('close-popup')
                        }
                    })
                    .catch((error) => {
                        $('#qrcode-button-cancel').css('pointer-events', 'all')
                        this.env.pos.get_order().is_calling_qrcode_payment = false
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                        })
                        return
                    })
            }
        }

        _onClickOpenPaymentGate() {
            window.open($('#url-mbpay-payment-gate').text())
        }

        async _onClickConfirmPaygateDetail() {
            document.getElementById('qrcode-button-confirm').style.pointerEvents = 'none'
            // clearInterval(interval___onClickConfirmPaygateDetail)
            let order_reference = this.env.pos.data_for_mbpay_paygate_detail[0][0]
            let merchant_id = this.env.pos.data_for_mbpay_paygate_detail[0][1]
            let pay_date = this.env.pos.data_for_mbpay_paygate_detail[0][2]
            let amount = this.env.pos.data_for_mbpay_paygate_detail[0][4]
            let params = {
                'mac_type': 'MD5',
                'mac': '',
                'merchant_id': merchant_id,
                'order_reference': order_reference,
                'pay_date': pay_date
            }
            let keys = Object.keys(params).sort()
            let inputMD5 = ''
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

            // Flag for check record payment_qrcode_transaction
            var transaction_flag = false
            // Request check record payment_qrcode_transaction
            await rpc.query({
                model: 'payment.qrcode.transaction',
                method: 'action_check_order_reference',
                args: [null, order_reference.slice(4, -4), amount]
            }, {
                timeout: 2000
            })
                .then((result) => {
                    $('#qrcode-button-confirm').css('pointer-events', 'all')
                    console.log('_onClickConfirmPaygateDetail action_check_order_reference', result)
                    if (result) {
                        transaction_flag = true
                        this.props.resolve({
                            result_api__mbpay_paygate_detail: true
                        })
                        this.trigger('close-popup')
                    }
                })
                .catch((error) => {
                    $('#qrcode-button-confirm').css('pointer-events', 'all')
                    document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                    this.env.pos.get_order().is_calling_qrcode_payment = false
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                    })
                    return
                })
            if (transaction_flag === false) {
                // Request API mbpay_paygate_detail
                rpc.query({
                    model: 'payment.qrcode.transaction',
                    method: 'action_api__mbpay_paygate_detail',
                    args: [null, params, inputMD5]
                }, {
                    timeout: 2000
                })
                    .then((result) => {
                        $('#qrcode-button-confirm').css('pointer-events', 'all')
                        console.log('_onClickConfirmPaygateDetail action_api__mbpay_paygate_detail', result)
                        if ((result['error_code'] === '00' && parseFloat(result['amount']) === amount) || result['error_code'] === '13') {
                            this.props.resolve({
                                result_api__mbpay_paygate_detail: true
                            })
                            this.trigger('close-popup')
                        } else {
                            $('#message-error-qrcode').css('display', 'inline-block')
                            $('#message-error-qrcode').text('Đơn hàng chưa được thanh toán')
                            setTimeout(() => {
                                $('#message-error-qrcode').css('display', 'none')
                            }, 2000)
                        }
                    })
                    .catch((error) => {
                        $('#qrcode-button-confirm').css('pointer-events', 'all')
                        document.getElementsByClassName('button next highlight')[0].style.pointerEvents = "all"
                        this.env.pos.get_order().is_calling_qrcode_payment = false
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Đã có lỗi xảy ra, vui lòng xem lại kết nối mạng hoặc cấu hình cần thiết.'),
                        })
                        return
                    })
            }
        }
    }

    QRCodePopup.template = 'QRCodePopup'
    Registries.Component.add(QRCodePopup)
    return QRCodePopup
})
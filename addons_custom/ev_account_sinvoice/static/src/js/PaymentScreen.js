odoo.define('ev_account_sinvoice.PaymentScreen', function (require) {
    'use strict'

    const core = require('web.core')
    const _t = core._t
    const Registries = require('point_of_sale.Registries')
    const PaymentScreen = require('point_of_sale.PaymentScreen')
    const {useListener} = require('web.custom_hooks')
    const rpc = require('web.rpc')

    let PaymentScreenSInvoice = PaymentScreen => class extends PaymentScreen {
        constructor(props) {
            super(...arguments);
            useListener('click-check-buyer-get-invoice', this._onClickCheckedBuyerGetInvoice)
            useListener('click-get-buyer-info-sinvoice', this._onClickGetBuyerInfoSInvoice)
            useListener('click-confirm-tax-code', this._onClickConfirmTaxCode)
        }

        _onClickCheckedBuyerGetInvoice() {
            var client = this.env.pos.get_client()
            if (!client) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Thông báo'),
                    body: this.env._t('Vui lòng chọn khách hàng để lấy hoá đơn điện tử'),
                })
                document.getElementById('x_buyer_get_invoice').checked = false
                return
            }
            var buyer_get_invoice = document.getElementById('x_buyer_get_invoice')
            if (buyer_get_invoice && buyer_get_invoice.checked) {
                this.currentOrder.set_is_get_invoice(true)
                document.getElementById('x_sinvoice').style.display = 'block'
            }
            if (buyer_get_invoice && !buyer_get_invoice.checked) {
                // clear data
                document.getElementById('x_sinvoice_vat').value = ''
                document.getElementById('x_sinvoice_company_name').value = ''
                document.getElementById('x_sinvoice_address').value = ''
                document.getElementById('x_sinvoice_email').value = ''

                this.currentOrder.set_is_get_invoice(false)
                document.getElementById('x_sinvoice').style.display = 'none'
            }
        }

        async _onClickGetBuyerInfoSInvoice() {
            console.log('_onClickGetBuyerInfoSInvoice')
            let partner = this.env.pos.get_client()
            await rpc.query({
                model: 'pos.order',
                method: 'get_partner_info_sinvoice',
                args: ['', partner.id.toString()]
            }).then((data) => {
                console.log(data)
                if (data !== undefined) {
                    document.getElementById('x_sinvoice_vat').value = data['sinvoice_vat']
                    document.getElementById('x_sinvoice_company_name').value = data['sinvoice_company_name']
                    document.getElementById('x_sinvoice_address').value = data['sinvoice_address']
                    document.getElementById('x_sinvoice_email').value = data['sinvoice_email']
                } else {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Không tìm thấy thông tin lấy hoá đơn gần nhất.'),
                    })
                    return
                }
            })
        }

        _onClickConfirmTaxCode() {
            console.log('_onClickConfirmTaxCode')
            let x_sinvoice_vat = document.getElementById('x_sinvoice_vat')
            let x_sinvoice_company_name = document.getElementById('x_sinvoice_company_name')
            let x_sinvoice_address = document.getElementById('x_sinvoice_address')
            let x_sinvoice_email = document.getElementById('x_sinvoice_email')
            let url_check_vat = 'url_check_vat'
            if (x_sinvoice_vat.value.trim()) {
                rpc.query({
                    model: 'account.sinvoice',
                    method: 'get_url_check_vat',
                    args: [null]
                }).then((res) => {
                    if (res) {
                        url_check_vat = res
                        let url = url_check_vat + x_sinvoice_vat.value.toString().trim()
                        $.ajax({
                            type: "GET",
                            url: url,
                            async: false,
                            success: (response) => {
                                if (response['code'] !== '00') {
                                    x_sinvoice_company_name.value = ''
                                    x_sinvoice_address.value = ''
                                    x_sinvoice_email.value = ''
                                    this.showPopup('ErrorPopup', {
                                        title: this.env._t('Thông báo'),
                                        body: this.env._t(response['desc']),
                                    })
                                    return
                                }
                                x_sinvoice_company_name.value = response['data']['name']
                                x_sinvoice_address.value = response['data']['address']
                                return
                            },
                            error: (err) => {
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t('Thông báo'),
                                    body: this.env._t(err),
                                })
                                return
                            },
                            timeout: 10000
                        })
                    } else {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Chưa cấu hình url check vat'),
                        })
                        return
                    }
                })
            } else {
                return
            }
        }

        async validateOrder(isForceValidate) {
            let order = this.currentOrder
            let x_sinvoice_vat = document.getElementById('x_sinvoice_vat')
            let x_sinvoice_company_name = document.getElementById('x_sinvoice_company_name')
            let x_sinvoice_address = document.getElementById('x_sinvoice_address')
            let x_sinvoice_email = document.getElementById('x_sinvoice_email')
            let x_buyer_get_invoice = document.getElementById('x_buyer_get_invoice')

            x_sinvoice_vat.value ? this.env.pos.get_order().x_sinvoice_vat = x_sinvoice_vat.value : null
            x_sinvoice_company_name.value ? this.env.pos.get_order().x_sinvoice_company_name = x_sinvoice_company_name.value : null
            x_sinvoice_address.value ? this.env.pos.get_order().x_sinvoice_address = x_sinvoice_address.value : null
            x_sinvoice_email.value ? this.env.pos.get_order().x_sinvoice_email = x_sinvoice_email.value : null

            if (x_buyer_get_invoice.checked) {
                if (x_sinvoice_vat.value) {
                    if (![10, 14].includes(x_sinvoice_vat.value.length) ||
                        (x_sinvoice_vat.value.length === 10 && !/^\d+$/.test(x_sinvoice_vat.value)) ||
                        (x_sinvoice_vat.value.length === 14 && !/^\d{10}-\d{3}$/.test(x_sinvoice_vat.value))) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Mã số thuế không hợp lệ. Mã số thuế phải là 10 chữ số hoặc 13 chữ số và dấu gạch ngang (-) ở sau chữ số thứ 10.'),
                        })
                        return
                    }
                }
                if (!x_sinvoice_company_name.value) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Vui lòng nhập tên công ty.'),
                    })
                    return
                }
                if (!x_sinvoice_address.value) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Vui lòng nhập địa chỉ.'),
                    })
                    return
                }
                if (!x_sinvoice_email.value) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Thông báo'),
                        body: this.env._t('Vui lòng nhập email.'),
                    })
                    return
                } else {
                    const regex = /^[ _A-Za-z0-9- \+]+(\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9]+)*(\.[A-Za-z]{2,})$/
                    if (!regex.test(x_sinvoice_email.value)) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Thông báo'),
                            body: this.env._t('Bạn đã nhập một email không hợp lệ.'),
                        })
                        return
                    }
                }
            }
            order.x_sinvoice_vat = x_sinvoice_vat.value.toString().trim()
            order.x_sinvoice_company_name = x_sinvoice_company_name.value.toString().trim()
            order.x_sinvoice_address = x_sinvoice_address.value.toString().trim()
            order.x_sinvoice_email = x_sinvoice_email.value.toString().trim()

            // Compute x_sinvoice_tax_amount
            let order_lines = order.get_orderlines()
            order_lines.forEach((line) => {
                let total_promotion = 0
                if (typeof line.x_is_price_promotion !== 'undefined') {
                    total_promotion += parseFloat(line.x_is_price_promotion)
                }
                if (typeof line.amount_promotion_total !== 'undefined') {
                    total_promotion += parseFloat(line.amount_promotion_total)
                }

                if (typeof line.amount_promotion_loyalty !== 'undefined') {
                    total_promotion += parseFloat(line.amount_promotion_loyalty)
                }
                let price_subtotal_incl = line.get_price_with_tax()
                if (!price_subtotal_incl) {
                    price_subtotal_incl = 0
                }
                // đưa tiền thuế sau km về 0 trước khi tính lại
                line.set_sinvoice_tax_amount(0)
                if (price_subtotal_incl > 0) {
                    let amount_after_tax = price_subtotal_incl - total_promotion
                    let taxes = line.get_applicable_taxes()
                    if (taxes) {
                        let vat_percent = taxes[0]['amount']
                        let vat_value = (vat_percent / 100)
                        let vat = 1 + vat_value
                        let qty = line.quantity
                        if (taxes[0]['price_include'] === true) {
                            let tax_amount = Math.round(((amount_after_tax / vat) * vat_value))
                            line.set_sinvoice_tax_amount(tax_amount)
                        } else {
                            let unit_price = line.price
                            let amount_untax = unit_price * qty
                            let tax_amount = Math.round((amount_untax * vat_percent) / 100)
                            line.set_sinvoice_tax_amount(tax_amount)
                        }
                    }
                }
            })
            super.validateOrder(isForceValidate)
        }
    }

    Registries.Component.extend(PaymentScreen, PaymentScreenSInvoice)
    return PaymentScreen
})
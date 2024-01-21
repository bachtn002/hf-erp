odoo.define('ev_pos_online.client_detail_edit', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    let ClientDetailsEditCustom = ClientDetailsEdit =>
        class extends ClientDetailsEdit {
            saveChanges() {
                this.env.pos.removePromotionsApplied();
                let processedChanges = {};
                for (let [key, value] of Object.entries(this.changes)) {
                    if (this.intFields.includes(key)) {
                        processedChanges[key] = parseInt(value) || false;
                    } else {
                        processedChanges[key] = value;
                    }
                }
                if (processedChanges.name === '') {
                    return this.showPopup('ErrorPopup', {
                        title: _('Tên khách hàng chưa nhập'),
                    });
                }
                if (!processedChanges.phone) {
                    return this.showPopup('ErrorPopup', {
                        title: _('Số điện thoại chưa nhập'),
                    });
                }
                var regEx = /^\d{4}-\d{2}-\d{2}$/;
                if (!regEx.test(processedChanges.date_of_birth) && processedChanges.date_of_birth) {
                    return this.showPopup('ErrorPopup', {
                        title: _('Định dạng ngày tháng năm không đúng'),
                    });
                }
                if (processedChanges.phone) {
                    if (processedChanges.phone.length > 15) {
                        return this.showPopup('ErrorPopup', {
                            title: _('Số điện thoại lớn hơn 15'),
                        });
                    }
                    var validNumber = "0123456789.-";
                    let check = true;

                    for (let i = 0; i < processedChanges.phone.length; i++) {
                        if (validNumber.indexOf(processedChanges.phone.charAt(i)) === -1) {
                            check = false
                        }
                    }
                    if (!check) {
                        return this.showPopup('ErrorPopup', {
                            title: 'Số điện thoại là số',
                        });
                    }
                    if (processedChanges.phone.length < 6) {
                        return this.showPopup('ErrorPopup', {
                            title: _('Số điện thoại nhỏ hơn 6'),
                        });
                    }
                    var search_string = processedChanges.phone;
                    try {
                        let search_string = processedChanges.phone;
                        this.env.pos.search_partner_to_phone(search_string);
                        this.render();
                    } catch (error) {
                        if (error === undefined) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Offline'),
                                body: this.env._t('Unable to search customer.'),
                            });
                        }
                    }
                    let result = this.env.pos.db.search_partner_limit(search_string)
                    let check_phone = false
                    result.forEach((re) => {
                        if (search_string === re.phone) {
                            check_phone = true
                        }
                    })
                    if (check_phone) {
                        this.showPopup('ErrorPopup', {
                            title: 'Số điện thoại đã tồn tại'
                        });
                        return
                    }
                    if (!check_phone) {
                        processedChanges.id = this.props.partner.id || false;
                        this.trigger('save-changes', {processedChanges});
                    }
                }
                // processedChanges.id = this.props.partner.id || false;
                // this.trigger('save-changes', {processedChanges});
            }

            // saveChanges() {
            //     console.log('check pos')
            //     let processedChanges = {};
            //     for (let [key, value] of Object.entries(this.changes)) {
            //         if (this.intFields.includes(key)) {
            //             processedChanges[key] = parseInt(value) || false;
            //         } else {
            //             processedChanges[key] = value;
            //         }
            //     }
            //     if ((!this.props.partner.name && !processedChanges.name) ||
            //         processedChanges.name === '') {
            //         return this.showPopup('ErrorPopup', {
            //             title: _('Tên khách hàng không được để trống'),
            //         });
            //     }
            //
            //     if ((!this.props.partner.phone && !processedChanges.phone) ||
            //         processedChanges.phone === '') {
            //         return this.showPopup('ErrorPopup', {
            //             title: _('Số điện thoại không được để trống'),
            //         });
            //     }
            //     processedChanges.id = this.props.partner.id || false;
            //     this.trigger('save-changes', {processedChanges});
            // }
        }

    Registries.Component.extend(ClientDetailsEdit, ClientDetailsEditCustom);

    return ClientDetailsEdit;

});
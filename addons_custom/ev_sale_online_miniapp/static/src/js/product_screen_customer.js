odoo.define('ev_sale_online_miniapp.ProductScreenCustomer', function (require) {
    'use strict'

    const ProductScreenCustomer = require('ev_pos_search_customer.ProductScreenCustomer')
    const Registries = require('point_of_sale.Registries')

    let ButtonCreateCustomer = ProductScreenCustomer => class extends ProductScreenCustomer {
        async _create_customer() {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            return this.env.pos.get_order().is_created_by_api ? null : (() => {
                if (this.env.pos.get_order().sale_online) {
                    if (is_not_allow_editing) {
                        return
                    } else {
                        super._create_customer()
                    }
                } else {
                    super._create_customer()
                }
            })()
        }

        async updateClientList(event) {
            let channel_current = self.posmodel.list_pos_channel_online.filter((i) => {
                return (i.id === this.env.pos.get_order().x_id_pos_channel_sale_online)
            })
            let is_not_allow_editing = false
            if (channel_current.length > 0) {
                is_not_allow_editing = channel_current[0]['is_not_allow_editing']
            }

            return this.env.pos.get_order().sale_online ? (() => {
                if (this.env.pos.get_order().is_created_by_api) {
                    return
                } else if (is_not_allow_editing) {
                    return
                } else {
                    this._removePromotionApplied__updateClientList(event)
                }
            })() : super.updateClientList(event)

        }

        _removePromotionApplied__updateClientList(event) {
            if (event.key !== 'Enter') {
                super.updateClientList(event)
                return
            }
            console.log(event.key)
            this.env.pos.removePromotionsApplied()
            super.updateClientList(event)
        }
    }
    Registries.Component.extend(ProductScreenCustomer, ButtonCreateCustomer)
    return ButtonCreateCustomer
})
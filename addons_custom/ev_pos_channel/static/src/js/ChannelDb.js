odoo.define('ev_pos_channel.DB', function (require) {
    'use strict'

    const PosDB = require('point_of_sale.DB')

    PosDB.include({
        addPosChannel: function (data) {
            this.save('pos_channel', data)
        },

        getPosChannelIds: function (data) {
            let row = this.load('pos_channel', [])
            return row.filter((item) => {
                return _.indexOf(data, item.id[0] != -1)
            })
        }

    })
    return PosDB
})
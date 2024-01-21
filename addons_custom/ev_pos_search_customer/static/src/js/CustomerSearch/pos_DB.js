odoo.define('ev_pos_search_customer.DB', function (require) {
    "use strict"

    var core = require('web.core');
    var utils = require('web.utils');
    const PosDB = require('point_of_sale.DB');

    PosDB.include({
        search_partner_limit: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(/ /g,'.+');
                var re = RegExp("([0-9]+):.*?"+utils.unaccent(query),"gi");
            }catch(e){
                return [];
            }
            var results = [];
            for(var i = 0; i < 7; i++){
                var r = re.exec(this.partner_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_partner_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        },
    });

    return PosDB;
})
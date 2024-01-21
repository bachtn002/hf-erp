odoo.define('ev_multi_barcode.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');
    var utils = require('web.utils');

    PosDB.include({
        init: function(options) {
            this._super(options);
            this.product_barcode_search_string = '';
            this.product_barcode_list = {};
            this.search_word=''
        },

        get_barcode_by_string: function (search_word){
            var barcodes = this.product_barcode_list
            for(var i = 0; i<barcodes.length; i++){
                if(search_word === barcodes[i].name){
                    this.search_word = ''
                    return barcodes[i];
                }
            }
        },

        save_multi_barcode: function(barcodes){
            var barcode_search_str = ""
            for(var i = 0; i < barcodes.length; i++){
                var str = '';
                if (barcodes[i].name){
                    str+= '|' + barcodes[i].name;
                }
                if (barcodes[i].product_id){
                    str = barcodes[i].product_id[0] + ':' + str.replace(/:/g, '') + '\n';
                }
                barcode_search_str += str
            }
            this.product_barcode_search_string += barcode_search_str
            this.product_barcode_list = barcodes
        },

        /* inherit function returns a list of products with :
         * - a category that is or is a child of category_id,
         * - a name, package or barcode containing the query (case insensitive)
         * - ADDITIONAL: in multi barcode list
         */
        search_product_in_category: function (category_id, query) {
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, '.');
                query = query.replace(/ /g, '.+');
                var re = RegExp("([0-9]+):.*?" + utils.unaccent(query), "gi");
            } catch (e) {
                return [];
            }
            var results = [];
            for (var i = 0; i < this.limit; i++) {
                var r = re.exec(this.category_search_string[category_id]);
                if (r) {
                    var id = Number(r[1]);
                    results.push(this.get_product_by_id(id));
                } else {
                    break;
                }
            }
            // search in multi_barcode list
            // if (results.length === 0) {
            this.search_word = query
            for (var i = 0; i < this.limit; i++) {
                var line = re.exec(this.product_barcode_search_string);
                if (line) {
                    var id = Number(line[1]);
                    results.push(this.get_product_by_id(id));
                } else {
                    break;
                }
            // }
            }
            // get unique products
            results = [...new Set(results)];
            return results;
        },
    });

    return PosDB;
})
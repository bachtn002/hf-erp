odoo.define('ev_stock_package.packed_client_action', function (require) {
'use strict';

var core = require('web.core');
var ClientAction = require('ev_stock_package.ClientAction');
var ViewsWidget = require('ev_stock_package.ViewsWidget');
const Dialog = require('web.Dialog');

var _t = core._t;

var PackageClientAction = ClientAction.extend({
    custom_events: _.extend({}, ClientAction.prototype.custom_events, {
        'change_location': '_onChangeLocation',
        'update_package_weight': '_updatePackageWeight',
    }),

    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.context = action.context;
        this.commands['O-BTN.validate'] = this._validate.bind(this);
        if (! this.actionParams.id) {
            console.log("change action params 222")
            this.actionParams.id = action.context.active_id;
            // model default (when page refreshed)
            this.actionParams.model = 'stock.package.transfer';
            this.actionParams.is_scan_product = true;
        }
        this.methods = {
            // cancel: 'action_cancel',
            validate: 'action_confirm',
        };
        this.viewInfo = 'stock_barcode.stock_picking_barcode';
        this.timeOut = 0;
    },

    willStart: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            // Bind the print slip command here to be able to pass the action as argument.
            // Get the usage of the picking type of `this.picking_id` to chose the mode between
            // `receipt`, `internal`, `delivery`.
            var picking_type_code = self.currentState.picking_type_code;
            var picking_state = self.currentState.state;
            if (picking_type_code === 'incoming') {
                self.mode = 'receipt';
            } else if (picking_type_code === 'outgoing') {
                self.mode = 'delivery';
            } else {
                self.mode = 'internal';
            }

            if (self.currentState.group_stock_multi_locations === false) {
                self.mode = 'no_multi_locations';
            }

            if (picking_state === 'done') {
                self.mode = 'done';
            } else if (picking_state === 'cancel') {
                self.mode = 'cancel';
            }
            self.allow_scrap = (
                (picking_type_code === 'incoming') && (picking_state === 'done') ||
                (picking_type_code === 'outgoing') && (picking_state !== 'done') ||
                (picking_type_code === 'internal')
            );

            self.isImmediatePicking = self.currentState.immediate_transfer;
            self.usablePackagesByBarcode = self.currentState.usable_packages || {};
            self._getTimeOut();
        });
    },

    start: function () {
        // this._onKeyDown = this._onKeyDown.bind(this);
        // this._onKeyUp = this._onKeyUp.bind(this);
        // this._toggleKeyEvents(true);
        return this._super(...arguments);
    },

    destroy: function () {
        // this._toggleKeyEvents(false);
        this._super();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Applies new destination or source location for all page's lines and then refresh it.
     *
     * @private
     * @param {number} locationId
     * @param {boolean} isSource true for the source, false for destination
     */
    _changeLocation: function (locationId, isSource) {
        const currentPage = this.pages[this.currentPageIndex];
        const sourceLocation = isSource ? locationId : currentPage.location_id;
        const destinationLocation = isSource ? currentPage.location_dest_id : locationId;
        const fieldName = isSource ? 'location_id' : 'location_dest_id';
        const currentPageLocationId = currentPage[fieldName];
        if (currentPageLocationId === locationId) {
            // Do nothing if the user try to change for the current page.
            return;
        }

        this.mutex.exec(() => {
            const locations = isSource ? this.sourceLocations : this.destinationLocations;
            const locationData = _.find(locations, (location) => location.id === locationId);
            // Apply the selected location on the page's lines.
            for (const line of currentPage.lines) {
                line[fieldName] = locationData;
            }
            return this._save().then(() => {
                // Find the page index (because due to the change, the page
                // could be to another place in the pages list).
                for (let i = 0; i < this.pages.length; i++) {
                    const page = this.pages[i];
                    if (page.location_id === sourceLocation &&
                        page.location_dest_id === destinationLocation) {
                        this.currentPageIndex = i;
                        break;
                    }
                }
                const prom = this._reloadLineWidget(this.currentPageIndex);
                this._endBarcodeFlow();
                return prom;
            });
        });
    },

    /**
     * Set timout to wait popup printing before show another popup
     */
    _getTimeOut : function (){
        var self = this;
        return this._rpc({
            model: 'stock.package.transfer',
            method: 'get_time_out_printing',
            args: [[this.actionParams.id]],
        }).then(function (value) {
            self.timeOut = value;
        });
    },

    /**
     * @override
     */
    _createLineCommand: function (line) {
        return [0, 0, {
            // picking_id: line.picking_id,
            product_id:  line.product_id.id,
            uom_id: line.uom_id[0],
            qty: line.qty,
            qty_done: line.qty_done,
            // location_id: line.location_id.id,
            // location_dest_id: line.location_dest_id.id,
            // lot_name: line.lot_name,
            // lot_id: line.lot_id && line.lot_id[0],
            // state: 'assigned',
            // owner_id: line.owner_id && line.owner_id[0],
            // package_id: line.package_id ? line.package_id[0] : false,
            // result_package_id: line.result_package_id ? line.result_package_id[0] : false,
            // dummy_id: line.virtual_id,
        }];
    },

    /**
     * @override
     */
    _getAddLineDefaultValues: function (currentPage) {
        const values = this._super(currentPage);
        values.default_location_dest_id = currentPage.location_dest_id;
        values.default_picking_id = this.currentState.id;
        values.default_qty_done = 1;
        return values;
    },

    /**
     * @override
     */
    _getLines: (state) => state.line_ids,

    /**
     * @override
     */
    _lot_name_used: function (product, lot_name) {
        var lines = this._getLines(this.currentState);
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            if (line.qty_done !== 0 && line.product_id.id === product.id &&
                (line.lot_name && line.lot_name === lot_name)) {
                return true;
            }
        }
        return false;
    },

    /**
     * @override
     */
    _getPageFields: function () {
        return [
            ['warehouse_id', 'warehouse_id.id'],
            ['warehouse_name', 'warehouse_id.display_name'],
            ['warehouse_dest_id', 'warehouse_dest_id.id'],
            ['warehouse_dest_name', 'warehouse_dest_id.display_name'],
        ];
    },

    /**
     * Return an array string representing the keys of `lines` objects the client action is
     * allowed to write on. It ll be used by `this._compareStates` to generate the write commands.
     * To implement by specialized client actions.
     *
     * @abstract
     * @private
     * @returns {Array} array of fields that can be scanned or modified
     */
    /**
     * @override
     */
    _getWriteableFields: function () {
        return ['qty','qty_done'];
    },

    /**
     * @override
     */
    _getLinesField: function () {
        return 'line_ids';
    },

    /**
     * @override
     */
    _getQuantityField: function () {
        return 'qty_done';
    },

    /**
     * @override
     */
    _instantiateViewsWidget: function (defaultValues, params) {
        // this._toggleKeyEvents(false);
        return new ViewsWidget(
            this,
            'stock.package.transfer.line',
            'ev_stock_package.stock_package_transfer_line_product_selector',
            defaultValues,
            params
        );
    },

    /**
     * @override
     */
    _isPickingRelated: function () {
        return true;
    },


    /**
     * @override
     */
    _makeNewLine: function (params) {
        var virtualId = this._getNewVirtualId();
        var currentPage = this.pages[this.currentPageIndex];
        var newLine = {
            'package_id': this.currentState.id,
            'product_id': {
                'id': params.product.id,
                'display_name': params.product.display_name,
                'barcode': params.barcode,
                'tracking': params.product.tracking,
                'is_package_cover': params.product.is_package_cover,
            },
            'product_barcode': params.barcode,
            'display_name': params.product.display_name,
            'qty': params.qty_done,
            'uom_id': params.product.uom_id,
            'qty_done': params.qty_done,
            'virtual_id': virtualId,
        };
        return newLine;
    },

    _checkPackageState: async function () {
        return await this._rpc({
            model: 'stock.package.transfer',
            method: 'get_current_package_state',
            args: [[this.currentState.id]]
        })
    },

    _openDialog: function () {
        var self = this;
        var message = _t("The package have confirm before, Please check again!");
        var buttons = [
            {
                text: _t("OK"),
                classes: 'btn-primary',
                close: true,
                click: function () {
                    return self.do_action(
                    {
                        type: 'ir.actions.act_window',
                        res_model: 'stock.transfer',
                        res_id: self.currentState.stock_transfer_id[0],
                        context: {
                            'active_id': self.currentState.stock_transfer_id[0]
                        },
                        views: [[false, 'form']],
                        target: 'current'
                    }, {
                        clear_breadcrumbs: true,
                    });
                }
            }
        ];

        return new Dialog(this, {
            size: 'medium',
            buttons: buttons,
            $content: $('<div>', {
                html: message,
            }),
            title: _t("Warning"),
        }).open();
    },

    /**
     * This method could open a wizard so it takes care of removing/adding the
     * "barcode_scanned" event listener.
     *
     * @override
     */
    _validate: async function (context) {
        const self = this;
        const superValidate = this._super.bind(this);
        var package_state = await self._checkPackageState();
        // if package already confirm then show popup waring and back to transfer
        if (['packaged', 'unpackaged'].includes(package_state)) {
            this._openDialog();
        }else {
        const timeout = this.timeOut || 1000
        this.mutex.exec(function () {
            const successCallback = function () {
                    Dialog.confirm(self, _t("Chose next action to continue!"), {
                    title: _t("Chose Navigate form"),
                    buttons: [
                        {
                            text: _t("Back to transfers"),
                            classes: 'btn-primary button_back_to_transfers',
                            close: true,
                            click: function () {
                                self.do_action('stock_barcode.stock_barcode_action_main_menu', {
                                    clear_breadcrumbs: true,
                                });
                            },
                        },
                        {
                            text: _t("Create new package"),
                            classes: 'btn-primary button_create_new_package',
                            close: true,
                            click: function () {
                                self._rpc({
                                    method: 'create_new_package',
                                    model: 'stock.transfer',
                                    args: [[self.currentState.stock_transfer_id[0]]],
                                }).then((package_id) => {
                                    if(!package_id){
                                        return self.do_action(
                                        {
                                            type: 'ir.actions.act_window',
                                            res_model: 'stock.transfer',
                                            res_id: self.currentState.stock_transfer_id[0],
                                            context: {
                                                'active_id': self.currentState.stock_transfer_id[0]
                                            },
                                            views: [[false, 'form']],
                                            target: 'current'
                                        }, {
                                            clear_breadcrumbs: true,
                                        });
                                    }
                                    var pack_id = package_id.replace(/\D/g, '');
                                    let url = window.location.href;
                                    let url_parts = url.split('&')
                                    for (var i = 0; i < url_parts.length; i++) {
                                        if (url_parts[i].includes('active_id')) {
                                            url = url.replace(url_parts[i], '');
                                            break;
                                        }
                                    }
                                    url = url + '&active_id=' + pack_id
                                    return self.do_action({
                                        type: 'ir.actions.act_url',
                                        url: url,
                                        target: 'self',
                                    }, {
                                        clear_breadcrumbs: true,
                                    });
                                })
                            },
                        },

                        {
                            text: _t("Go Back"),
                            close: true,
                            click: function () {
                                return self.do_action(
                                {
                                    type: 'ir.actions.act_window',
                                    res_model: 'stock.transfer',
                                    res_id: self.currentState.stock_transfer_id[0],
                                    context: {
                                        'active_id': self.currentState.stock_transfer_id[0]
                                    },
                                    views: [[false, 'form']],
                                    target: 'current'
                                },{
                                    clear_breadcrumbs: true,
                                });
                            },
                        }
                    ],
                })
                self.displayNotification({
                    message: _t("The package has been validated"),
                    type: 'success',
                });
            };

            return superValidate(context).then(async (res) => {
                await new Promise(resolve => setTimeout(resolve, timeout));
                if (res) {
                    core.bus.off('barcode_scanned', self, self._onBarcodeScannedHandler);
                   return successCallback();
                }
            })
        });
        }
    },

    /**
     * Enables or disables the `keydown` and `keyup` event.
     * They are toggled when passing through the form view (edit or add a line).
     *
     * @param {boolean} mustBeActive
     */
    _toggleKeyEvents: function (mustBeActive) {
        // if (mustBeActive) {
        //     document.addEventListener('keydown', this._onKeyDown);
        //     document.addEventListener('keyup', this._onKeyUp);
        // } else {
        //     document.removeEventListener('keydown', this._onKeyDown);
        //     document.removeEventListener('keyup', this._onKeyUp);
        // }
    },

    /**
     * @override
     */
    _updateLineCommand: function (line) {
        return [1, line.id, {
            qty : line.qty,
            qty_done : line.qty_done,
            // location_id: line.location_id.id,
            // location_dest_id: line.location_dest_id.id,
            // lot_id: line.lot_id && line.lot_id[0],
            // lot_name: line.lot_name,
            // owner_id: line.owner_id && line.owner_id[0],
            // package_id: line.package_id ? line.package_id[0] : false,
            // result_package_id: line.result_package_id ? line.result_package_id[0] : false,
        }];
    },

    // -------------------------------------------------------------------------
    // Private: flow steps
    // -------------------------------------------------------------------------

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handles the `change_location` OdooEvent. It will change location for move lines.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onChangeLocation: function (ev) {
        ev.stopPropagation();
        this._changeLocation(ev.data.locationId, ev.data.isSource);
    },

    /**
     * Listens for shift key being pushed for display the remaining qty instead of only the "+1".
     *
     * Assumptions:
     * - We don't need to worry about Caps Lock being active because it's a huge pain to detect
     *   and probably can't be until the first letter is pushed.
     *
     * @private
     * @param {KeyboardEvent} keyDownEvent
     */
    _onKeyDown: function (keyDownEvent) {
        if (this.linesWidget && keyDownEvent.key === 'Shift' &&
            !keyDownEvent.repeat && !keyDownEvent.ctrlKey && !keyDownEvent.metaKey) {
            this.linesWidget._applyShiftKeyDown();
        }
    },

    /**
     * Listens for shift being released to only display the "+1". There's no
     * reliable way to distinguish between 1 or 2 shift buttons being pushed (without
     * a tedious tracking variable), so let's assume the user won't push both down at
     * the same time and still expect it to work properly.
     *
     * @private
     * @param {KeyboardEvent} keyUpEvent
     */
    _onKeyUp: function (keyUpEvent) {
        if (this.linesWidget && keyUpEvent.key === 'Shift') {
            this.linesWidget._applyShiftKeyUp();
        }
    },

    /**
     * Handles the `print_picking` OdooEvent. It makes an RPC call
     * to the method 'do_print_picking'.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onPrintPicking: function (ev) {
        ev.stopPropagation();
        this._printPicking();
    },

    /**
     * @override
     */
    _onReload: function (ev) {
        this._super(...arguments);
        // this._toggleKeyEvents(true);
    },


    /**
     * Save weight of package
     *
     * @private
     * @param {OdooEvent} ev
     */
    _updatePackageWeight: function () {
        var self = this;
        var def;
        var pack_weight = document.getElementById('package_weight').value
        def = this._rpc({
            'route': '/ev_stock_package/get_set_barcode_view_state',
            'params': {
                'record_id': self.currentState.id,
                'mode': 'write',
                'model_name': 'stock.package.transfer',
                'write_vals': pack_weight,
                'write_field': 'weight',
            },
        });
        return def;
    },
});

core.action_registry.add('stock_barcode_package_client_action', PackageClientAction);

return PackageClientAction;

});

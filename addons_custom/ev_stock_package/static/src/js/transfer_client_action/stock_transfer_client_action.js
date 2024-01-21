odoo.define('ev_stock_package.stock_transfer_client_action', function (require) {
'use strict';

var core = require('web.core');
var ClientAction = require('ev_stock_package.ClientAction');
var ViewsWidget = require('ev_stock_package.ViewsWidget');

var _t = core._t;

var PackageClientAction = ClientAction.extend({
    custom_events: _.extend({}, ClientAction.prototype.custom_events, {
        'change_location': '_onChangeLocation',
    }),

    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.context = action.context;
        this.commands['O-BTN.validate'] = this._validate.bind(this);
        if (! this.actionParams.id) {
            console.log("change action params 111")
            this.actionParams.id = action.context.active_id;
            this.actionParams.model = 'stock.transfer';
        }
        this.methods = {
            // cancel: 'action_cancel',
            validate: 'action_validate_scan',
        };
        this.viewInfo = 'stock_barcode.stock_picking_barcode';
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
     * @override
     */
    _createLineCommand: function (line) {
        return [0, 0, {
            // picking_id: line.picking_id,
            product_id:  line.product_id.id,
            uom_id: line.uom_id[0],
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
    // _getState: function () {
    //     console.log("************_getState****************")
    //     console.log()
    //     const superProm = this._super(...arguments);
    //     if (this.groups.group_tracking_lot) {
    //         // If packages are enabled, checks to add new `result_package_id` as usable package.
    //         superProm.then(res => {
    //             this.usablePackagesByBarcode = res[0].usable_packages;
    //         });
    //     }
    //     return superProm;
    // },

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
        return ['qty_done'];
    },

    /**
     * @override
     */
    _getLinesField: function () {
        return 'transfer_scan_line';
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
        if (params['isPackageline']) {
            if (this.actionParams.state !== 'transfer') {
                return new ViewsWidget(
                    this,
                    'stock.package.transfer',
                    'ev_stock_package.stock_package_transfer_selector_out',
                    defaultValues,
                    params)
            } else {
                return new ViewsWidget(
                    this,
                    'stock.package.transfer',
                    'ev_stock_package.stock_package_transfer_selector_in',
                    defaultValues,
                    params)
            }
        } else {
            return new ViewsWidget(
                this,
                'stock.transfer.line',
                'ev_stock_package.stock_transfer_line_selector',
                defaultValues,
                params
            )
        }
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
            'picking_id': this.currentState.id,
            'product_id': {
                'id': params.product.id,
                'display_name': params.product.display_name,
                'barcode': params.barcode,
                'tracking': params.product.tracking,
            },
            'product_barcode': params.barcode,
            'display_name': params.product.display_name,
            'product_uom_qty': 0,
            'product_uom_id': params.product.uom_id,
            'qty_done': params.qty_done,
            'location_id': {
                'id': currentPage.location_id,
                'display_name': currentPage.location_name,
            },
            'location_dest_id': {
                'id': currentPage.location_dest_id,
                'display_name': currentPage.location_dest_name,
            },
            'package_id': params.package_id,
            'result_package_id': params.result_package_id,
            // 'owner_id': params.owner_id,
            'state': 'assigned',
            'reference': this.name,
            'virtual_id': virtualId,
            'owner_id': params.owner_id,
        };
        return newLine;
    },

    /**
     * This method could open a wizard so it takes care of removing/adding the
     * "barcode_scanned" event listener.
     *
     * @override
     */
    _validate: function (context) {
        const self = this;
        const superValidate = this._super.bind(this);
        this.mutex.exec(function () {
            const successCallback = function () {
                self.displayNotification({
                    message: _t("The transfer has been validated"),
                    type: 'success',
                });
                self.trigger_up('exit');
            };
            const exitCallback = function (infos) {
                if ((infos === undefined || !infos.special) && this.dialog.$modal.is(':visible')) {
                    successCallback();
                }
                core.bus.on('barcode_scanned', self, self._onBarcodeScannedHandler);
            };

            return superValidate(context).then((res) => {
                if (_.isObject(res)) {
                    const options = {
                        on_close: exitCallback,
                    };
                    core.bus.off('barcode_scanned', self, self._onBarcodeScannedHandler);
                    return self.do_action(res, options);
                } else {
                    return successCallback();
                }
            });
        });
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
        //1 means updates an existing record of id, id with the values in values.
        return [1, line.id, {
            qty_done : line.qty_done,
            product_id: line.product_id ? line.product_id["id"]: false,
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
     * @override
     */
    _onReload: function (ev) {
        this._super(...arguments);
        // this._toggleKeyEvents(true);
    },
});

core.action_registry.add('stock_barcode_transfer_client_action', PackageClientAction);

return PackageClientAction;

});

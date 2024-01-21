odoo.define('ev_stock_package.ClientAction', function (require) {
'use strict';

var concurrency = require('web.concurrency');
var core = require('web.core');
const Dialog = require('web.Dialog');
var AbstractAction = require('web.AbstractAction');
var BarcodeParser = require('barcodes.BarcodeParser');

var ViewsWidget = require('ev_stock_package.ViewsWidget');
var HeaderWidget = require('ev_stock_package.HeaderWidget');
var LinesWidget = require('ev_stock_package.LinesWidget');
// var LinesWidget = require('stock_barcode.LinesWidget');
// var SettingsWidget = require('stock_barcode.SettingsWidget');
var utils = require('web.utils');
var ajax = require('web.ajax');

var _t = core._t;
var QWeb = core.qweb;

function isChildOf(locationParent, locationChild) {
    return _.str.startsWith(locationChild.parent_path, locationParent.parent_path);
}

var ClientAction = AbstractAction.extend({
    custom_events: {
        // show_information: '_onShowInformation',
        // show_settings: '_onShowSettings',
        exit: '_onExit',
        edit_line: '_onEditLine',
        increment_line: '_onIncrementLine',
        add_line: '_onAddLine',
        remove_line: '_onRemoveLine',
        // next_page: '_onNextPage',
        // previous_page: '_onPreviousPage',
        reload: '_onReload',
        // cancel: '_onCancel',
        validate: '_onValidate',
        listen_to_barcode_scanned: '_onListenToBarcodeScanned',
        ask_confirmation: '_onAskConfirmation',
    },
    events: {
        'click .o_exit': '_onClickExit'
    },

    /**
     * Set times printing
     */
    _getTimesPrinting : function (){
        var self = this;
        return this._rpc({
            model: 'stock.package.transfer',
            method: 'get_times_printing',
            args: [[this.actionParams.id]],
        }).then(function (value) {
            self.timesPrinting = value ;
        });
    },


    /**
     * Handles the click on the `print button`.
     *
     * @private
     * @param report_name: template name want to print
     * @param id: id of record want to print
     * @param type: pdf
     */

    _triggerDownload: function(report_name, id, type) {
        var id_path = ''
        if(this.timesPrinting > 1){
            for(var i=0; i<this.timesPrinting; i++){
                id_path += id.toString() + ","
            }
            id_path = '/' + id_path.slice(0, -1)
        }else{
            id_path = '/' + id.toString();
        }
        console.log("id_path")
        console.log(id_path)
        return new Promise(function (resolve) {
            if (type === 'pdf') {
                ajax.rpc('/report/pdf_custom/' + report_name + id_path, {}).then(function (result) {
                    if (result) {
                        resolve(true);
                        printJS({printable: result, type: 'pdf', base64: true})
                    }
                });
                resolve(false);
            }
        })
    },

    /**
     * Handles the click on the `exit button`.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onClickExit: function (ev) {
        ev.stopPropagation();
        var self = this;
        var transfer_id = null;
        if(this.actionParams.model === 'stock.package.transfer'){
            transfer_id = self.currentState.stock_transfer_id[0]
        }
        if(this.actionParams.model === 'stock.transfer'){
            transfer_id = self.currentState.id
        }
        if(transfer_id !== null){
            var view_promise = this._rpc({
                method: 'get_view_transfer',
                model: 'stock.transfer',
                args: [[transfer_id]]
            })
            view_promise.then(function (view_id) {
                core.bus.off('barcode_scanned', self, self._onBarcodeScannedHandler);
                return self.do_action(
                    {
                        type: 'ir.actions.act_window',
                        res_model: 'stock.transfer',
                        res_id: transfer_id,
                        context: {
                            'active_id': transfer_id
                        },
                        views: [[view_id, 'form']],
                        target: 'current'
                    },{
                        clear_breadcrumbs: true,
                    });
                }
            )
        }else return false;
    },

    init: function (parent, action) {
        this._super.apply(this, arguments);

        // We keep a copy of the action's parameters in order to make the calls to `this._getState`.
        this.actionParams = {
            id: action.params.package_id,
            model: action.params.model,
            state: action.params.state,
            is_scan_product: action.params.is_scan_product,
        };

        // Temp patch for the height issue
        this.actionManager = parent;
        this.actionManagerInitHeight = this.actionManager.$el.height;
        this.actionManager.$el.height('100%');
        this.discardingPackageCover = null;
        this.typeErrors = {
            invalidBarcode: false,
            invalidQuantity: false
        };

        this.mutex = new concurrency.Mutex();

        this.commands = {
            'O-CMD.PREV': this._previousPage.bind(this),
            'O-CMD.NEXT': this._nextPage.bind(this),
            'O-CMD.PAGER-FIRST': this._firstPage.bind(this),
            'O-CMD.PAGER-LAST': this._lastPage.bind(this),
            'O-CMD.MAIN-MENU': this._onMainMenu.bind(this),
        };

        // State variables
        this.initialState = {};     // Will be filled by getState.
        this.stepState = {};        // Will be filled at the start of each step.
        this.currentState = {};     // Will be filled by getState and updated when operations occur.
        this.pages = [];            // Groups separating the pages.
        this.currentPageIndex = 0;  // The displayed page index related to `this.pages`.
        // this.groups = {};
        this.title = this.actionParams.model === 'stock.transfer' ? // title of
            _t('Transfer  ') : _t('Transfer'); // the main navbar
        this.title = this.actionParams.model === 'stock.package.transfer' ? // title of
            _t('Package Transfer ') : ''; // the main navbar

        this.mode = undefined;      // supported mode: `receipt`, `internal`, `delivery`, `inventory`
        this.scannedLocation = undefined;
        this.scannedLines = [];
        this.scannedLocationDest = undefined;
        this.timesPrinting = 1;

        // Steps
        this.currentStep = undefined;
        this.stepsByName = {};
        for (var m in this) {
            if (typeof this[m] === 'function' && _.str.startsWith(m, '_step_')) {
                this.stepsByName[m.split('_step_')[1]] = this[m].bind(this);
            }
        }
    },

    willStart: function () {
        var self = this;
        return Promise.all([
            self._super.apply(self, arguments),
            self._getState(this.actionParams.id),
            // get all product and barcode
            self._getProductBarcodes(),
            // get all package transfer
            self._getPackageTransferByBarcode(),
            self._getTimesPrinting(),
        ]).then(function () {
            return self._loadNomenclature();
        });
    },

    start: function () {
        var self = this;
        this.$('.o_content').addClass('o_barcode_client_action');
        core.bus.on('barcode_scanned', this, this._onBarcodeScannedHandler);

        this.headerWidget = new HeaderWidget(this);
        // this.settingsWidget = new SettingsWidget(this, this.actionParams.model, this.mode, this.allow_scrap);
        return this._super.apply(this, arguments).then(function () {
            return Promise.all([
                self.headerWidget.prependTo(self.$('.o_content')),
                // self.settingsWidget.appendTo(self.$('.o_content'))
            ]).then(function () {
                // self.settingsWidget.do_hide();
                return self._save();
            }).then(function () {
                return self._reloadLineWidget(self.currentPageIndex);
            });
        });
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScannedHandler);
        this._super();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Makes the rpc to model's method to cancel the record.
     *
     * @private
     */
    _cancel: function () {
        return this._save().then(() => {
            return this._rpc({
                model: this.actionParams.model,
                method: this.methods.cancel,
                args: [[this.currentState.id]],
            });
        });
    },

    /**
     * Define and return a formatted command to create a new line in the record.
     *
     * @abstract
     * @private
     * @param {Object} line
     * @returns {Array}
     */
    _createLineCommand: function (line) {
        throw new Error(_t('_createLineCommand is an abstract method. You need to implement it.'));
    },

    _discard: function () {
        this.currentState = this.stepState;
        return Promise.resolve();
    },

    _beep: function () {
        if (typeof(Audio) !== "undefined") {
            var snd = new Audio();
            snd.src = "/ev_stock_package/static/src/sounds/error.wav";
            snd.play();
        }
    },

    /**
     * Returns default values used to instantiate `ViewsWidget` and create a new line.
     *
     * @param {Object} currentPage
     * @returns {Object}
     */
    _getAddLineDefaultValues: function (currentPage) {
        return {
            default_company_id: this.currentState.company_id[0],
            default_location_id: currentPage.location_id,
        };
    },

    /**
     * Make an rpc to get the state and afterwards set `this.currentState` and `this.initialState`.
     * It also completes `this.title`. If the `state` argument is passed, use it instead of doing
     * an extra RPC.
     *
     * @private
     * @param {Object} [recordID] Id of the active picking or inventory adjustment.
     * @param {Object} [state] state
     * @return {Promise}
     */
    _getState: function (recordId, state) {
        var self = this;
        var def;
        if (state) {
            def = Promise.resolve(state);
        } else {
            def = this._rpc({
                'route': '/ev_stock_package/get_set_barcode_view_state',
                'params': {
                    'record_id': recordId,
                    'mode': 'read',
                    'model_name': self.actionParams.model,
                },
            });
        }
        return def.then(function (res){
            self.currentState = res[0];
            self.initialState = $.extend(true, {}, res[0]);
            self.title += self.initialState.display_name;
            self.groups = {};
            self.show_entire_packs = false;
            if (self._isPickingRelated()) {
                self.sourceLocations = self.currentState.warehouse_id;
                self.destinationLocations = self.currentState.warehouse_dest_id;
            }
            return res;
        });
    },

    /**
     * Make an rpc to get the products barcodes and afterwards set `this.productsByBarcode`.
     *
     * @private
     * @return {Promise}
     */
    _getProductBarcodes: function () {
        var self = this;
        return this._rpc({
            'model': 'product.product',
            'method': 'get_all_products_by_barcode',
            'args': [],
        }).then(function (res) {
            self.productsByBarcode = res;
        });
    },

    /**
     * Make a rpc to get the stock.package.transfer name and afterwards set `this.packageTransferByBarcode`.
     *
     * @private
     * @return {Promise}
     */
    _getPackageTransferByBarcode: function () {
        var self = this;
        return this._rpc({
            'model': 'stock.package.transfer',
            'method': 'get_all_package_by_name',
            'args': [],
        }).then(function (res) {
            self.packageTransferByBarcode = res;
        });
    },

    _loadNomenclature: function () {
        // barcode nomenclature
        this.barcodeParser = new BarcodeParser({'nomenclature_id': this.currentState.nomenclature_id});
        if (this.barcodeParser) {
            return this.barcodeParser.load();
        }
    },

    _isProduct: function (barcode) {
        var parsed = this.barcodeParser.parse_barcode(barcode);
        if (parsed.type === 'weight') {
            var product = this.productsByBarcode[parsed.base_code];
            // if base barcode is not a product, error will be thrown in _step_product()
            if (product) {
                product.qty = parsed.value;
            }
            return product;
        } else {
            // search product by barcode and return it if exist
            return this.productsByBarcode[parsed.code];
        }
    },

    _isPackageTransfer: function (barcode) {
        // search product by barcode and return it if exist
        return this.packageTransferByBarcode[barcode];
    },

    /**
     * Return an unique location, even if the model have a x2m field.
     * Could also return undefined if it's from an inventory adjustment with no
     * locations.
     *
     * @returns {Object|undefined}
     */
    _getLocationId: function () {
        return this.currentState.location_id || this.currentState.location_ids[0];
    },

    /**
     * Return an array of objects representing the lines displayed in `this.linesWidget`.
     * To implement by specialized client action.
     * actions.
     *
     * @abstract
     * @private
     * @returns {Array} array of objects (lines) to be displayed
     */
    _getLines: function (state) {  // jshint ignore:line
        return [];
    },

    /**
     * Instantiates a `ViewsWidget`. As the widget is similar for the different
     * client action but used on different models and views, this method must be
     * overrided to specify right model and view.
     * Used to create new line or edit an existing one.
     *
     * @abstract
     * @param {Object} defaultValues
     * @param {Object} params
     * @returns {ViewsWidget}
     */
    _instantiateViewsWidget: function (defaultValues, params) {
        throw new Error(_t('_instantiateViewsWidget is an abstract method. You need to implement it.'));
    },

    /**
     * Return true if the given lot_name for the product is already present.
     *
     * @abstract
     * @private
     * @param {Object} product
     * @param {string} lot_name
     *
     * @returns {Boolean}
     */
    _lot_name_used: function (product, lot_name) {
        return false;
    },

    /**
     * Return an array of string used to group the lines into pages. The string are keys the
     * `lines` objects.
     * To implement by specialized client actions.
     *
     * @abstract
     * @private
     * @returns {Array} array of fields to group (a group is actually a page)
     */
    _getPageFields: function () {
        return [];
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
    _getWriteableFields: function () {
        return [];
    },

    /**
     * Return the name of the lines field used by the model.
     *
     * @abstract
     * @private
     * @returns {string}
     */
    _getLinesField: function () {
        throw new Error(_t('_getLinesField is an abstract method. You need to implement it.'));
    },

    /**
     * Return the name of the field used by the model's line.
     *
     * @abstract
     * @private
     * @returns {string}
     */
    _getQuantityField: function () {
        throw new Error(_t('_getQuantityField is an abstract method. You need to implement it.'));
    },

    /**
     * Will compare `this._getLines(this.initialState)` and `this._getLines(this.currentState)` to
     * get created or modified lines. The result of this method will be used by `this._applyChanges`
     * to actually make the RPC call that will write the update values to the database.
     *
     * New lines are always pushed at the end of `this._getLines(this.currentState)`, so we assume
     * all lines having a greater index than the higher one in `_getLines(this.initialState)` are
     * new.
     *
     * @private
     * @returns {Array} array of objects representing the new or modified lines
     */
    _compareStates: function () {
        var modifiedMovelines = [];
        var writeableFields = this._getWriteableFields();

        // Get the modified lines.
        for (var i = 0; i < this._getLines(this.initialState).length; i++) {
            var currentLine = this._getLines(this.currentState)[i];
            var initialLine = this._getLines(this.initialState)[i];
            for (var j = 0; j < writeableFields.length; j++) {
                var writeableField = writeableFields[j];
                if (!_.isEqual(utils.into(initialLine, writeableField), utils.into(currentLine, writeableField))) {
                    modifiedMovelines.push(currentLine);
                    break;
                }
            }
        }
        // Get the new lines.
        if (this._getLines(this.initialState).length < this._getLines(this.currentState).length) {
            modifiedMovelines = modifiedMovelines.concat(
                this._getLines(this.currentState).slice(this._getLines(this.initialState).length)
            );
        }
        return modifiedMovelines;
    },

    /**
     * Build a list of command from `changes` and make the `write` rpc.
     * To implement by specialized client actions.
     *
     * @private
     * @param {Array} changes lines in the current record needing to be created or updated
     * @returns {Promise} resolved when the rpc is done ; failed if nothing has to be updated
     */
    _applyChanges: function (changes) {
        const formattedCommands = [];
        for (const line of changes) {
            let cmd;
            if (line.id) {
                cmd = this._updateLineCommand(line);
            } else {
                cmd = this._createLineCommand(line);
            }
            formattedCommands.push(cmd);
        }
        if (formattedCommands.length > 0){
            const params = {
                mode: 'write',
                model_name: this.actionParams.model,
                record_id: this.currentState.id,
                write_vals: formattedCommands,
                write_field: this._getLinesField(),
            };

            return this._rpc({
                route: '/ev_stock_package/get_set_barcode_view_state',
                params: params,
            });
        } else {
            return Promise.reject();
        }
    },

    /**
     * This method will return a list of pages with grouped by source and destination locations from
     * `this.currentState.lines`. We may add pages not related to the lines in the following cases:
     *   - if there isn't any lines yet, we create a group with the default source and destination
     *     location of the picking
     *   - if the user scanned a different source location than the one in the current page, we'll
     *     create a page with the scanned source location and the default destination location of
     *     the picking.
     *
     * We do not need to apply the second logic in the case the user scans a destination location
     * in a picking client action as the lines will be impacted before calling this method.
     *
     * This method will *NOT* update `this.currentPageIndex`.
     *
     * @private
     * @returns {Array} array of objects representing the pages
     */
    _makePages: function () {
        var pages = [];
        var defaultPage = {};
        var self = this;
        if (this._getLines(this.currentState).length) {
            defaultPage = {
                lines: this._getLines(this.currentState),
                warehouse_id: this.currentState.warehouse_id.id,
                warehouse_name: this.currentState.warehouse_id.display_name,
                warehouse_dest_id: this.currentState.warehouse_dest_id.id,
                warehouse_dest_name: this.currentState.warehouse_dest_id.display_name,
            };
        };
        pages.push(defaultPage);
        return pages;
    },

    /**
     * String identifying lines created in the client actions.

     * @private
     * @returns {string}
     */
    _getNewVirtualId: function () {
        return _.uniqueId('virtual_line_');
    },

    /**
     * Helper to create a new line.
     * To implement by specialized client actions.
     *
     * @abstract
     * @private
     * @param {Object} params attributes of the line (model depending, see implementation)
     * @returns {Object} created line
     */
    _makeNewLine: function (params) {
        return {};
    },

    /**
     * Refresh the displayed page/lines on the screen. It destroys and reinstantiate
     * `this.linesWidget`.
     *
     * @private
     * @param {Object} pageIndex page index
     * @returns {Promise}
     */
     _reloadLineWidget: function (pageIndex) {
        var self = this
        if (this.linesWidget) {
            this.linesWidget.destroy();
        }
        var nbPages = this.pages.length;
        this.linesWidget = new LinesWidget(this, this.pages[pageIndex], pageIndex, nbPages);
        return this.linesWidget.appendTo(this.$('.o_content')).then(function() {
            // In some cases, we want to restore the GUI state of the linesWidget
            // (on a reload not calling _endBarcodeFlow)
            if (self.linesWidgetState) {
                self.linesWidget.highlightLocation(self.linesWidgetState.highlightLocationSource);
                self.linesWidget.highlightDestinationLocation(self.linesWidgetState.highlightLocationDestination);
                self.linesWidget._toggleScanMessage(self.linesWidgetState.scan_message);
                delete self.linesWidgetState;
            }
            if (self.lastScannedPackage) {
                self.linesWidget.highlightPackage(self.lastScannedPackage);
                delete self.lastScannedPackage;
            }
        });
    },

    /**
     * Main method to make the changes done in the client action persistent in the database through
     * RPC calls. It'll compare `this.currentState` to `this.initialState`, make an RPC with the
     * commands generated by the previous step, re-read the `this.model` state, re-prepare the
     * groups and move `this.currentIndex` to the page of the same group. It also tries to not make
     * an RPC if there aren't changes to save.
     *
     * @private
     * @param {Object} params.forceReload boolean to know if we want to force a read even if no
     *   changes were found.
     * @param {Object} params.new_location_id new source location on the line
     * @param {Object} params.new_location_dest_id new destinationlocation on the line
     * @returns {Promise}
     */
    _save: function (params) {
        params = params || {};
        var self = this;

        // keep a reference to the currentGroup
        var currentPage = this.pages[this.currentPageIndex];
        if (! currentPage) {
            currentPage = {};
        }

        // var currentLocationId = currentPage.location_id;
        // var currentLocationDestId = currentPage.location_dest_id;


        // make a write with the current changes
        var recordId = this.actionParams.id;
        var applyChangesDef =  this._applyChanges(this._compareStates()).then(function (state) {

            // Fixup virtual ids in `self.scanned_lines`
            var virtual_ids_to_fixup = _.filter(self._getLines(state[0]), function (line) {
                return line.dummy_id;
            });
            _.each(virtual_ids_to_fixup, function (line) {
                if (self.scannedLines.indexOf(line.dummy_id) !== -1) {
                    self.scannedLines = _.without(self.scannedLines, line.dummy_id);
                    self.scannedLines.push(line.id);
                }
            });

            return self._getState(recordId, state);
        }, function (error) {
            // on server error, let error be displayed and do nothing
            if (error !== undefined) {
                return Promise.reject();
            }
            if (params.forceReload) {
                return self._getState(recordId);
            } else {
                return Promise.resolve();
            }
        });

        return applyChangesDef.then(function () {
            self.pages = self._makePages();
            // var newPageIndex = _.findIndex(self.pages, function (page) {
            //     return page.location_id === (params.new_location_id || currentLocationId) &&
            //         (self.actionParams.model === 'stock.inventory' ||
            //         page.location_dest_id === (params.new_location_dest_id || currentLocationDestId));
            // }) || 0;
            // if (newPageIndex === -1) {
            //     newPageIndex = 0;
            // }
            self.currentPageIndex = 0;
        });
    },

    /**
     * Handles the actions when a barcode is scanned, mainly by executing the appropriate step. If
     * we need to change page after the step is executed, it calls `this._save` and
     * `this._reloadLineWidget` with the new page index. Afterwards, we apply the appropriate logic
     * to `this.linesWidget`.
     *
     * @private
     * @param {String} barcode the scanned barcode
     * @returns {Promise}
     */
    _onBarcodeScanned: function (barcode) {
        var self = this;
        return this.stepsByName[this.currentStep || 'source'](barcode, []).then(function (res) {
            /* We check now if we need to change page. If we need to, we'll call `this.save` with the
             * `new_location_id``and `new_location_dest_id` params so `this.currentPage` will
             * automatically be on the new page. We need to change page when we scan a source or a
             * destination location ; if the source or destination is different than the current
             * page's one.
             */
            var prom = Promise.resolve();
            var currentPage = self.pages[self.currentPageIndex];
            if (
                (self.scanned_location &&
                 ! self.scannedLines.length &&
                 self.scanned_location.id !== currentPage.location_id
                ) ||
                (self.scanned_location_dest &&
                 self.scannedLines.length &&
                 self.scanned_location_dest.id !== currentPage.location_dest_id
                )
            ) {
                // The expected locations are the scanned locations or the default picking locations.
                var expectedLocationId = self.scanned_location.id;
                var expectedLocationDestId;
                if (self.actionParams.model === 'stock.picking'){
                    expectedLocationDestId = self.scanned_location_dest &&
                                             self.scanned_location_dest.id ||
                                             self.currentState.location_dest_id.id;
                }

                if (expectedLocationId !== currentPage.location_id ||
                    expectedLocationDestId !== currentPage.location_dest_id
                ) {
                    var params = {
                        new_location_id: expectedLocationId,
                    };
                    if (expectedLocationDestId) {
                        params.new_location_dest_id = expectedLocationDestId;
                    }
                    prom = self._save(params).then(function () {
                        return self._reloadLineWidget(self.currentPageIndex);
                    });
                }
            }

            // Apply now the needed actions on the different widgets.
            if (self.scannedLines && self.scanned_location_dest) {
                self._endBarcodeFlow();
            }
            var linesActions = res.linesActions;
            var always = function () {
                _.each(linesActions, function (action) {
                    action[0].apply(self.linesWidget, action[1]);
                });
            };
            prom.then(always).guardedCatch(always);
            return prom;
        }, function (errorMessage) {
            var invalidQuantity = self.typeErrors.invalidQuantity;
            var invalidBarcode = self.typeErrors.invalidBarcode;
            self.typeErrors.invalidQuantity = false;
            self.typeErrors.invalidBarcode = false;
            self._beep();
            if(invalidQuantity){
                // self._beep();
                self._overScanQuantity(barcode);
            }
            else if(invalidBarcode){
                self._onAskConfirmation(barcode);
            }else{
                self._onAskConfirmation(barcode);
            }
            return Promise.reject();
        });
    },

    /**
     * Clear the states variables of the barcode flow. It should be used before beginning a new
     * flow.
     *
     * @private
     */
    _endBarcodeFlow: function () {
        this.scanned_location = undefined;
        this.scannedLines = [];
        this.scanned_location_dest = undefined;
        this.currentStep = undefined;
    },

    /**
     * Loop over the lines displayed in the current pages and try to find a candidate to increment
     * according to the `params` argument.
     *
     * @private
     * @param {Object} params information needed to find the candidate line
     * @param {Object} params.package
     * @param {Object} params.product
     * @param {Object} params.lot_id
     * @param {Object} params.lot_name
     * @returns object|boolean line or false if nothing match
     */
    _findCandidateLineToIncrement: function (params) {
        var product = params.product;
        // var lotId = params.lot_id;
        // var lotName = params.lot_name;
        var packageId = params.package;
        var currentPage = this.pages[this.currentPageIndex];
        var res = false;
        for (var z = 0; z < currentPage.lines.length; z++) {
            var lineInCurrentPage = currentPage.lines[z];
            if (product) {
                if (lineInCurrentPage.product_id) {
                    if (lineInCurrentPage.product_id.id === product.id){
                        if (lineInCurrentPage.product_uom_qty && lineInCurrentPage.qty_done >= lineInCurrentPage.product_uom_qty) {
                            continue;
                        }
                        res = lineInCurrentPage;
                        break;
                    }
                }
            }
            if (packageId){
                if (lineInCurrentPage.package_id === packageId.id) {
                    res = lineInCurrentPage;
                }
            }
        }
        return res;
    },

    /**
     * Main method called when a quantity needs to be incremented or a lot set on a line.
     * it calls `this._findCandidateLineToIncrement` first, if nothing is found it may use
     * `this._makeNewLine`.
     *
     * @private
     * @param {Object} params information needed to find the potential candidate line
     * @param {Object} params.product
     * @param {Object} params.lot_id
     * @param {Object} params.lot_name
     * @param {Object} params.package_id
     * @param {Object} params.result_package_id
     * @param {Boolean} params.doNotClearLineHighlight don't clear the previous line highlight when
     *     highlighting a new one
     * @return {object} object wrapping the incremented line and some other informations
     */
    _incrementLines: function (params) {
        var line = this._findCandidateLineToIncrement(params);
        var isNewLine = false;
        var showErrorIncreasePackageCoverLine = false;
        var errorMessage;
        var check_qty_before_update = 0
        if (line) {
            if(params.product){
                //Case tem cân ký sẽ truyền thêm qty
                check_qty_before_update += (params.product.qty || 1) + line.qty_done
            }else if(params.package){
                check_qty_before_update += (params.package.qty || 1) + line.qty_done
            }
            if(check_qty_before_update > line.qty && this.actionParams.model === 'stock.transfer' && this.actionParams.state === 'transfer'){
                errorMessage = _t("Quantity receiving can not be greater than quantity delivery");
            }else{
                //if there is a line contain a package cover and quantity done is greater than zero then show error
                if (params.product){
                    // Update the line with the processed quantity.
                    if (this._isPickingRelated()) {
                        if(params.product.is_package_cover && line.qty_done > 0){
                            // if exist a line package cover then keep old quantity done
                            showErrorIncreasePackageCoverLine = true
                        }else{
                            line.qty_done += params.product.qty || 1;
                        }
                        if (params.package_id) {
                            line.package_id = params.package_id;
                        }
                        if (params.result_package_id) {
                            line.result_package_id = params.result_package_id;
                        }
                    }
                }else if(params.package){
                    // Update the line with the processed quantity.
                    if(this.actionParams.model === 'stock.transfer'){
                        // Package delivery
                        if(line.qty_done >= 1){
                            errorMessage = _("Package can be add more than 1 quantity.");
                        }else{
                            line.qty_done += params.package.qty || 1;
                        }
                    }
                }
            }
        } else if (params.product) {
            // Create a line with the processed quantity.
            if (this._isAbleToCreateNewLine(params.product.is_package_cover)) {
                isNewLine = true;
                params.qty_done = params.product.qty || 1;
                line = this._makeNewLine(params);
                this._getLines(this.currentState).push(line);
                // this.pages[this.currentPageIndex].lines.push(line);
            }
        }
        return {
            'id': line.id,
            'virtualId': line.virtual_id,
            'lineDescription': line,
            'isNewLine': isNewLine,
            'errorMessage': errorMessage,
            'showErrorIncreasePackageCoverLine': showErrorIncreasePackageCoverLine,
        };
    },

    /**
     * Defines if the model is able to create new lines on the fly.
     *
     * @private
     * @returns {boolean}
     */
    _isAbleToCreateNewLine: function (is_package_cover) {
        return this.actionParams.model === 'stock.package.transfer' && is_package_cover;
    },

    /**
     * Defines if the lines widget will must display control buttons.
     *
     * @private
     * @returns {boolean}
     */
    _isControlButtonsEnabled: function () {
        return this.mode !== 'done' && this.mode !== 'cancel';
    },

    /**
     * Defines if the lines widget will must display optionnal buttons
     * ('Add product' and 'Put In Pack' buttons).
     *
     * @returns {boolean}
     */
    _isOptionalButtonsEnabled: function () {
        return true;
    },

    /**
     * Returns `true` if the model is related to transfers.
     *
     * @private
     * @returns {boolean}
     */
    _isPickingRelated: function () {
        return false;
    },

    /**
     * Define and return a formatted command to update a record line.
     *
     * @abstract
     * @private
     * @param {Object} line
     * @returns {Array}
     */
    _updateLineCommand: function (line) {
        throw new Error(_t('_updateLineCommand is an abstract method. You need to implement it.'));
    },

    _check_package_scanned: function(lines) {
        let is_using_cover = false;
        for (var i =0 ; i < lines.length; i++) {
            if (lines[i].product_id.is_package_cover){
                is_using_cover = true
                return true;
            }
        }
        return false;

    },

    /**
     * Save weight of package
     *
     * @private
     * @param {OdooEvent} ev
     */
    _updatePackageWeight: function () {
        throw new Error(_t('_updateLineCommand is an abstract method. You need to implement it.'));
    },

    /**
     * Makes the rpc to the validate method of the model.
     *
     * @private
     * @returns {Promise}
     */
    _validate: function (context) {
        var self = this;
        if(this.actionParams.model === 'stock.transfer'){
            return this._save().then(() => {
            return this._rpc({
                model: this.actionParams.model,
                method: this.methods.validate,
                context: context || {},
                args: [[this.currentState.id]],
            });
        });
        }else {
            // Before validate package/transfer we need to save changes of current state
            // Call backend validate corresponding to model after that
            // Check package cover scanned or not, show Notify if not scanned
            if (this._check_package_scanned(this.currentState.line_ids)) {
                this._updatePackageWeight().then(() => {
                    var template = 'ev_stock_package.report_template_stamp_package_view'
                    self._triggerDownload(template, self.actionParams.id, 'pdf')
                })
                return this._save().then(() => {
                    this._rpc({
                        model: this.actionParams.model,
                        method: this.methods.validate,
                        context: context || {},
                        args: [[this.currentState.id]],
                    })
                    return true;
                })
            } else {
                var message = _t("Package cover has not been scanned. Do you still want to proceed?");
                this.discardingPackageCover = new Promise(function (resolve, reject) {
                    var dialog = Dialog.confirm(self, message, {
                        title: _t("Warning"),
                        confirm_callback: () => {
                            self.discardingPackageCover = null;
                            self._updatePackageWeight().then(() => {
                                var template = 'ev_stock_package.report_template_stamp_package_view'
                                self._triggerDownload(template, self.actionParams.id, 'pdf')
                            })
                            resolve(true);
                            return self._save().then(() => {
                                self._rpc({
                                    model: self.actionParams.model,
                                    method: self.methods.validate,
                                    context: context || {},
                                    args: [[self.currentState.id]],
                                })
                            });
                        },
                        cancel_callback: () => {
                            self.discardingPackageCover = null;
                            self.unblockScanSreen();
                            resolve(false);
                        },
                    });
                    //Block scan even
                    self.blockScanSreen();
                    dialog.on('closed', self.discardingPackageCover, reject);
                });
                return this.discardingPackageCover;
            }
        }
    },

    // -------------------------------------------------------------------------
    // Private: flow steps
    // -------------------------------------------------------------------------

    /**
     * Handle what needs to be done when a source location is scanned.
     *
     * @param {string} barcode scanned barcode
     * @param {Object} linesActions
     * @returns {Promise}
     */
    _step_source: function (barcode, linesActions) {
        var self = this;
        this.currentStep = 'source';
        this.stepState = $.extend(true, {}, this.currentState);
        var errorMessage;
        return this._step_product(barcode, linesActions).then(function (res) {
            return Promise.resolve({linesActions: res.linesActions});
        }, function (specializedErrorMessage) {
            delete self.scanned_location;
            self.currentStep = 'source';
            if (specializedErrorMessage){
                return Promise.reject(specializedErrorMessage);
            }
            return Promise.reject();
        });
    },

    /**
     * @private
     * @returns {Promise}
     */
    _onAskConfirmation(barcode) {
        // After dialog open => remove even scan barcode - prevent receive scan action from user
        // And remove button close => force user click OK button
        // When button OK clicked => reattach barcode scan even handler
        var self = this;
        var buttons = [
            {
                text: _t("OK"),
                classes: 'btn-primary-custom',
                close: true,
                click: function () {
                    self.unblockScanSreen();
                },
            }
        ];
        var dialog = new Dialog(this, {
            size: 'medium',
            title: _t("Warning"),
            buttons: buttons,
            $content: QWeb.render('NoBarcodeFound', {'barcode': barcode}),
        });
        dialog.opened().then(function () {
            self.blockScanSreen();
            document.querySelector(".close").remove()
        })
        return dialog.open();
    },

    /**
     * @private
     * @returns {Promise}
     */
    _overScanQuantity(barcode) {
        // After dialog open => remove even scan barcode - prevent receive scan action from user
        // And remove button close => force user click OK button
        // When button OK clicked => reattach barcode scan even handler
        var self = this;
        var buttons = [
            {
                text: _t("OK"),
                classes: 'btn-primary-custom',
                close: true,
                click: function () {
                    self.unblockScanSreen();
                },
            }
        ];
        var dialog = new Dialog(this, {
            size: 'medium',
            title: _t("Warning"),
            buttons: buttons,
            $content: QWeb.render('OverScanQuantity', {'barcode': barcode}),
        });
        dialog.opened().then(function () {
            self.blockScanSreen();
            document.querySelector(".close").remove()
        })
        return dialog.open();
    },

    blockScanSreen: function (){
        // remove event barcode_scanned handlers attached
        core.bus.off('barcode_scanned', this, this._onBarcodeScannedHandler);
    },

    unblockScanSreen: function (){
       // remove event barcode_scanned handlers attached
       core.bus.on('barcode_scanned', this, this._onBarcodeScannedHandler);
    },

    /**
     * Handle what needs to be done when a product is scanned.
     *
     * @param {string} barcode scanned barcode
     * @param {Object} linesActions
     * @returns {Promise}
     */
    _step_product: function (barcode, linesActions) {
        var self = this;
        this.currentStep = 'product';
        this.stepState = $.extend(true, {}, this.currentState);
        var errorMessage;
        if (self.actionParams.is_scan_product){
            // if product is not exist, we find package if exist pass package into params to _incrementLine
            var product = this._isProduct(barcode);
            if (product) {
                var res = this._incrementLines({'product': product, 'barcode': barcode});
                //if there is a line contain a package cover and quantity done is greater than zero then show error
                if (res.showErrorIncreasePackageCoverLine){
                    self.typeErrors.invalidQuantity = true;
                    return Promise.reject();
                }
                errorMessage = res.errorMessage
                if (errorMessage){
                    self.typeErrors.invalidQuantity = true;
                    return Promise.reject();
                }
                if (res.isNewLine && product.is_package_cover) {
                    linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
                } else if (!(res.id || res.virtualId)) {
                    self.typeErrors.invalidBarcode = true;
                    return Promise.reject();
                } else {
                    if (product.tracking === 'none') {
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, this.actionParams.model]]);
                    } else {
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, 0, this.actionParams.model]]);
                    }
                }
                this.scannedLines.push(res.id || res.virtualId);
                return Promise.resolve({linesActions: linesActions});
            }
        }else {
            var package_transfer = this._isPackageTransfer(barcode);
            if (package_transfer) {
                var pack_line = this._incrementLines({'package': package_transfer, 'barcode': barcode});
                errorMessage = pack_line.errorMessage
                if (errorMessage){
                    self.typeErrors.invalidQuantity = true;
                    return Promise.reject();
                    // return Promise.reject(errorMessage);
                }
                else if(!(pack_line.id || pack_line.virtualId)) {
                    self.typeErrors.invalidBarcode = true;
                    return Promise.reject();
                    // return Promise.reject(_("There are no lines to increment."));
                } else {
                    linesActions.push([this.linesWidget.incrementProduct, [pack_line.id || pack_line.virtualId, pack_line.qty || 1, this.actionParams.model]]);
                }
                this.scannedLines.push(pack_line.id || pack_line.virtualId);
                return Promise.resolve({linesActions: linesActions});
            }
        }
        return Promise.reject();
    },

    /**
     * Helper used when we want to go the next page. It calls `this._endBarcodeFlow`.
     *
     * @return {Promise}
     */
    _nextPage: function (){
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                if (self.currentPageIndex < self.pages.length - 1) {
                    self.currentPageIndex++;
                }
                var prom =  self._reloadLineWidget(self.currentPageIndex);
                self._endBarcodeFlow();
                return prom;
            });
        });
    },

    /**
     * Helper used when we want to go the previous page. It calls `this._endBarcodeFlow`.
     *
     * @return {Promise}
     */
    _previousPage: function () {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                if (self.currentPageIndex > 0) {
                    self.currentPageIndex--;
                } else {
                    self.currentPageIndex = self.pages.length - 1;
                }
                var prom = self._reloadLineWidget(self.currentPageIndex);
                self._endBarcodeFlow();
                return prom;
            });
        });
    },
    /**
     * Helper used when we want to go the first page. It calls `this._endBarcodeFlow`.
     * @private
     * @returns {Promise}
     */
    _firstPage: function () {
        var self = this;
        return self._save().then(function () {
            if (self.currentPageIndex !== 0) {
                self.currentPageIndex = 0;
                self._endBarcodeFlow();
                return self._reloadLineWidget(0);
            }
        });
    },
    /**
     * Helper used when we want to go the last page. It calls `this._endBarcodeFlow`.
     * @private
     * @returns {Promise}
     */
    _lastPage: function () {
        var self = this;
        return self._save().then(function () {
            if (self.currentPageIndex !== self.pages.length - 1) {
                self.currentPageIndex = self.pages.length - 1;
                var prom = self._reloadLineWidget(self.pages.length - 1);
                self._endBarcodeFlow();
                return prom;
            }
        });
    },


    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handles the barcode scan event. Dispatch it to the appropriate method if it is a
     * commande, else use `this._onBarcodeScanned`.
     *
     * @private
     * @param {String} barcode scanned barcode
     */
    _onBarcodeScannedHandler: function (barcode) {
        //TODO
        var self = this;
        this.mutex.exec(function () {
            if (self.mode === 'done' || self.mode === 'cancel') {
                self.do_warn(false, _t('Scanning is disabled in this state'));
                return Promise.resolve();
            }
            var commandeHandler = self.commands[barcode];
            if (commandeHandler) {
                return commandeHandler();
            }
            return self._onBarcodeScanned(barcode)
        });
    },

    /**
     * Handles the `cancel` OdooEvent.
     *
     * @private
     * @param {OdooEvent} ev
     * @returns {Promise}
     */
    // _onCancel: function (ev) {
    //     ev.stopPropagation();
    //     this._cancel();
    // },

    /**
     * Handles the `exit` OdooEvent. We disable the fullscreen mode and trigger_up an
     * `history_back`.
     *
     * @private
     * @param {OdooEvent} ev
     */
     _onExit: function (ev) {
        ev.stopPropagation();
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                self.actionManager.$el.height(self.actionManagerInitHeight);
                self.trigger_up('history_back');
            });
        });
    },

    /**
     * Handles the `add_product` OdooEvent. It destroys `this.linesWidget` and displays an instance
     * of `ViewsWidget` for the line model.
     * `this.ViewsWidget`
     *
     * @private
     * @param {OdooEvent} ev
     */
     _onAddLine: function (ev) {
        ev.stopPropagation();
        this.mutex.exec(() => {
            this.linesWidgetState = this.linesWidget.getState();
            this.linesWidget.destroy();
            this.headerWidget.toggleDisplayContext('specialized');
            // Get the default locations before calling save to not lose a newly created page.
            var currentPage = this.pages[this.currentPageIndex];
            var defaultValues = this._getAddLineDefaultValues(currentPage);
            return this._save().then(() => {
                this.ViewsWidget = this._instantiateViewsWidget(defaultValues);
                return this.ViewsWidget.appendTo(this.$('.o_content'));
            });
        });
    },

    /**
     * Handles the `remove_line` OdooEvent.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onRemoveLine: function (ev) {
        var self = this;
        ev.stopPropagation();
        var virtual_id = _.isString(ev.data.id) ? ev.data.id : false;
        if(virtual_id){
            const lines = this.pages[this.currentPageIndex].lines;
            const line = lines.find(l => virtual_id === (l.id || l.virtual_id));
            this._getLines(this.currentState).pop(line)
            return self.trigger_up('reload');
        } else {
            self._rpc({
                model: 'stock.package.transfer.line',
                method: 'unlink',
                args: [[ev.data.id]],
            }).then(function () {
                return self.trigger_up('reload');
            });
        }
    },

    /**
     * Handles the `edit_product` OdooEvent. It destroys `this.linesWidget` and displays an instance
     * of `ViewsWidget` for the line model.
     *
     * Editing a line should not "end" the barcode flow, meaning once the changes are saved or
     * discarded in the opened form view, the user should be able to scan a destination location
     * (if the current flow allows it) and enforce it on `this.scanned_lines`.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onEditLine: function (ev) {
        ev.stopPropagation();
        this.linesWidgetState = this.linesWidget.getState();
        this.linesWidget.destroy();
        // FIXME this.headerWidget.toggleDisplayContext is not a function
        // this.headerWidget.toggleDisplayContext('specialized');

        // If we want to edit a not yet saved line, keep its virtual_id to match it with the result
        // of the `applyChanges` RPC.
        var virtual_id = _.isString(ev.data.id) ? ev.data.id : false;

        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                var id = ev.data.id;
                var is_package_line = ev.data.is_package_line;
                // Todo edit new line added
                if (virtual_id) {
                    var currentPage = self.pages[self.currentPageIndex];
                    var rec = _.find(currentPage.lines, function (line) {
                        return line.dummy_id === virtual_id;
                    });
                    id = rec.id;
                }

                self.ViewsWidget = self._instantiateViewsWidget({}, {currentId: id, isPackageline: is_package_line});
                return self.ViewsWidget.appendTo(self.$('.o_content'));
            });
        });
    },

    /**
     * Handles the 'increment_line' OdooEvent. From a line (`LinesWidget`), it
     * will increase the quantity of the corresponding line.
     *
     * @abstract
     * @param {OdooEvent} ev
     * @param {integer} ev.data.id id on the line to increment
     * @param {integer} [ev.data.qty] quantity to increase (1 by default)
     */
    _onIncrementLine: function (ev) {
        ev.stopPropagation();
        const id = ev.data.id;
        const qty = ev.data.qty || 1;
        const line = this._getLines(this.currentState).find(l => id === (l.id || l.virtual_id));
        line[this._getQuantityField()] += qty;
        // Add the line like if user scanned it to be able to find it if user
        // will scan the same product after.
        this.scannedLines.push(id);
        this.linesWidget.incrementProduct(id, qty, this.actionParams.model, true);
    },

    /**
     * Handles the `reload` OdooEvent.
     * Currently, this event is only triggered by `this.ViewsWidget`.
     *
     * @private
     * @param {OdooEvent} ev ev.data could contain res_id
     */
    _onReload: function (ev) {
        ev.stopPropagation();
        if (this.ViewsWidget) {
            this.ViewsWidget.destroy();
        }
        // if (this.settingsWidget) {
        //     this.settingsWidget.do_hide();
        // }
        // this.headerWidget.toggleDisplayContext('init');
        // this.$('.o_show_information').toggleClass('o_hidden', true);
        var self = this;
        this._save({'forceReload': true}).then(function () {
            var record = ev.data.record;
            // depending on record source, location_id may not be included, so avoid throwing an error in this case
            if (record && record.data.location_id) {
                var newPageIndex = _.findIndex(self.pages, function (page) {
                    return page.location_id === record.data.location_id.res_id &&
                           (self.actionParams.model === 'stock.inventory' ||
                            page.location_dest_id === record.data.location_dest_id.res_id);
                });
                if (newPageIndex === -1) {
                    new Error('broken');
                }
                self.currentPageIndex = newPageIndex;

                // Add the edited/added product in `this.scannedLines` if not already present. The
                // goal is to impact them on the potential next step.
                if (self.scannedLines.indexOf(record.data.id) === -1) {
                    self.scannedLines.push(record.data.id);
                }
            }

            self._reloadLineWidget(self.currentPageIndex);
            self.$('.o_show_information').toggleClass('o_hidden', false);
        });
    },

    /**
     * Handles the `next_move` OdooEvent. It makes `this.linesWidget` display
     * the next group of lines.
     *
     * @private
     * @param {OdooEvent} ev
     */
    // _onNextPage: function (ev) {
    //     ev.stopPropagation();
    //     this._nextPage();
    // },

    /**
     * Handles the `previous_move` OdooEvent. It makes `this.linesWidget` display
     * the previous group of lines.
     *
     * @private
     * @param {OdooEvent} ev
     */
    // _onPreviousPage: function (ev) {
    //     ev.stopPropagation();
    //     this._previousPage();
    // },

    /**
     * Handles the 'main_menu' OdooEvent. It's used when we want to go back the
     * main app menu.
     * @private
     */
    _onMainMenu: function () {
        var self = this;
        self._save().then(function () {
            self.do_action('stock_barcode.stock_barcode_action_main_menu', {
                clear_breadcrumbs: true,
            });
        });
    },

    /**
     * Handles the 'listen_to_barcode_scanned' OdooEvent.
     *
     * @private
     * @param {OdooEvent} ev ev.data.listen
     */
    _onListenToBarcodeScanned: function (ev) {
        if (ev.data.listen) {
            core.bus.on('barcode_scanned', this, this._onBarcodeScannedHandler);
        } else {
            core.bus.off('barcode_scanned', this, this._onBarcodeScannedHandler);
        }
    },

    /**
     * Handles the `validate` OdooEvent. It makes an RPC call
     * to the method 'action_confirm' to validate the current picking
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onValidate: function (ev) {
        ev.stopPropagation();
        this._validate();
    },

});

core.action_registry.add('barcode_package_client_action', ClientAction);

return ClientAction;

});

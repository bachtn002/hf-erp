odoo.define('ev_pos_promotion.tests_PromotionPopup', function (require) {
    "use strict"

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const testUtils = require('web.testUtils');
    // const testUtils = require('web.test_utils');
    const makePosTestEnv = require('point_of_sale.test_env');
    const PopupControllerMixin = require('point_of_sale.PopupControllerMixin');
    const {xml} = owl.tags;


    QUnit.module('PromotionPopup_components_test', {
        before() {
            class Root extends PopupControllerMixin(PosComponent) {
                /*static template = xml`
                        <div>
                            <t t-if="popup.isShow" t-component="popup.component" t-props="popupProps" t-key="popup.name"/>
                        </div>
                    `;*/
            }

            Root.env = makePosTestEnv();
            this.Root = Root;
            Registries.Component.freeze();
        }
    }, function () {

        QUnit.test('PromotionPopup', async function (assert) {
            assert.expect(1);

            const root = new this.Root();
            await root.mount(testUtils.prepareTarget());

            let promotions = [{
                name: 'Mua 10tr giam 20% tối đa 500k'
            }]

            root.showPopup('PromotionPopup', {promotions: promotions});
            await testUtils.nextTick();

            assert.strictEqual(root.el.querySelectorAll('li.o_ev_pos_promotion__promotion-item').length, 1);

            root.unmount();
            root.destroy();

        });

    });

});

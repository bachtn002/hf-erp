odoo.define('ev_pos_toggle_numpad.ToggleCategoryButton', function(require){
  "use strict";

  const PosComponent = require('point_of_sale.PosComponent');
  const Registries = require('point_of_sale.Registries');
  const { useState } = owl.hooks;


  class ToggleCategoryButton extends PosComponent {

		constructor(){
      super(...arguments);
			this.state = useState({isShow: true});
		}

    onClick = (ev) => {
			ev.preventDefault();
			$('.products-widget-control').toggleClass('hide-content');
			this.state.isShow = !this.state.isShow;
		}
	};

	ToggleCategoryButton.template = 'ToggleCategoryButton';

	Registries.Component.add(ToggleCategoryButton);

	return ToggleCategoryButton;

});

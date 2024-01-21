odoo.define('ev_pos_toggle_numpad.ToggleNumpadButton', function(require){
  "use strict";

  const PosComponent = require('point_of_sale.PosComponent');
  const Registries = require('point_of_sale.Registries');
  const { useState } = owl.hooks;


  class ToggleNumpadButton extends PosComponent {

		constructor(){
      super(...arguments);
			this.state = useState({isShow: true});
		}

    onClick = (ev) => {
			ev.preventDefault();
			$('div.subpads').slideToggle();
			this.state.isShow = !this.state.isShow;
		}
	};

	ToggleNumpadButton.template = 'ToggleNumpadButton';

	Registries.Component.add(ToggleNumpadButton);

	return ToggleNumpadButton;

});

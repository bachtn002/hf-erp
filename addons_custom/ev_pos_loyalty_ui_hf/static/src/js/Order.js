odoo.define('ev_pos_loyalty_ui.Order', function(require){
	"use strict"

	const models = require('point_of_sale.models');

	var _superOrder = models.Order;
	models.Order = models.Order.extend({
		apply_reward: function(reward){
			_superOrder.prototype.apply_reward.call(this, reward);
			this.trigger('apply-reward');
		},

		set_client: function(client){
			_superOrder.prototype.set_client.call(this, client);
			let self = this;
			let rewardLines = this.orderlines.filter((line)=>{
				return line.reward_id;
			});
			rewardLines.forEach((line)=>{
				self.remove_orderline(line);
			});
		}

	});

	return models;

});

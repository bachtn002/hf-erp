from odoo import models


class QueueJob(models.Model):
    _inherit = "queue.job"

    def _message_post_on_failure(self):
        # loại bỏ queue zns False k gửi mail
        if self.model_name in ('zns.information', 'data.webhook.zns'):
            return
        return super(QueueJob, self)._message_post_on_failure()

from . import CronJob

class ExpireExpiredProducts(CronJob):

    title = "Expire published products that have an expiration date in the past."

    def run(self):
        self.log("Expired N items")
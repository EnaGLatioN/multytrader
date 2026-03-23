from analytics.models import Analytics


class AnalyticsTracker:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.obj = Analytics(*args, **kwargs)
            cls._instance.long_ids = []
            cls._instance.short_ids = []
        return cls._instance

    @classmethod
    def update(cls, **kwargs):
        if cls._instance:
            for key, value in kwargs.items():
                setattr(cls._instance.obj, key, value)

    @classmethod
    def update_ex(cls, ready_order_for_send):
        for key, item in ready_order_for_send.items():
            for order in item:
                if key == 'LONG':
                    cls._instance.long_ids.append(order.exchange_id)
                else:
                    cls._instance.short_ids.append(order.exchange_id)

    @classmethod
    def save_and_clear(cls):
        if cls._instance and cls._instance.obj:
            cls._instance.obj.save()
            
            if cls._instance.long_ids:
                cls._instance.obj.exchange_long.set(cls._instance.long_ids)
            if cls._instance.short_ids:
                cls._instance.obj.exchange_short.set(cls._instance.short_ids)
            
            cls._instance = None
    
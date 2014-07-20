# -*- coding: utf-8 -*-
from functools import wraps
from django.db.models.signals import post_save, post_delete


class Observer(object):
    """
    An observer observes the model given in init.
    It provides some properties and functions in order to know what's happening in the database.
    """
    def __init__(self, model):
        self.model = model
        self.objects_created = []
        self.objects_updated = []
        self.objects_deleted = []

    @property
    def number_of_objects_created(self):
        return len(set(self.objects_created))

    @property
    def number_of_objects_updated(self):
        return len(set(self.objects_updated))

    @property
    def number_of_objects_deleted(self):
        return len(set(self.objects_deleted))

    @property
    def nothing_has_changed(self):
        return self.number_of_objects_created + \
            self.number_of_objects_updated + \
            self.number_of_objects_deleted == 0

    def monkey_patch_test(self, test):
        """
        Add to the test method a property to access the observer easily.
        """
        observer_name = "{}_observer".format(self.model.__name__).lower()
        setattr(test, observer_name, self)

    def object(self, instance):
        """
        Monkey patch the given model instance with is_created, is_updated, is_deleted and is_untouched properties
        """
        instace_id = instance.id or getattr(instance, 'old_id', None)
        instance.is_created = instace_id in self.objects_created
        instance.is_updated = instace_id in self.objects_updated
        instance.is_deleted = instace_id in self.objects_deleted
        instance.is_untouched = not instance.is_created and not instance.is_updated and not instance.is_deleted
        return instance

    def connect(self):
        """connect Django signals"""
        post_save.connect(self.save_receiver, self.model, dispatch_uid="observe_post_save_model_{}".format(self.model.__name__))
        post_delete.connect(self.delete_receiver, self.model, dispatch_uid="observe_post_delete_model_{}".format(self.model.__name__))

    def disconnect(self):
        """disconnect Django signals"""
        post_save.disconnect(self.save_receiver, self.model, dispatch_uid="observe_post_save_model_{}".format(self.model.__name__))
        post_delete.disconnect(self.delete_receiver, self.model, dispatch_uid="observe_post_delete_model_{}".format(self.model.__name__))

    def save_receiver(self, sender, instance=None, created=False, **kwargs):
        """receiver for save and update signals"""
        if created:
            self.objects_created.append(instance.id)
        else:
            self.objects_updated.append(instance.id)

    def delete_receiver(self, sender, instance=None, **kwargs):
        """receiver for delete signal"""
        self.objects_deleted.append(instance.id)
        instance.old_id = instance.id


def observe_models(*models):
    """
    Decorator used to add model observers to function/method decorated
    :param models: the models to be observed
    """
    def decorator(test_method):
        @wraps(test_method)
        def wrapper(this, *args, **kwargs):
            this.observers = dict()
            # connect signals
            for model in models:
                observer = Observer(model)
                observer.connect()
                this.observers[model] = observer
                # add this.modelname_observer property
                observer.monkey_patch_test(this)
            # add default observer
            if len(models) == 1:
                this.observer = this.observers[models[0]]

            # execute test itesef
            test_method(this, *args, **kwargs)

            # disconnect all signals
            for observer in this.observers.values():
                observer.disconnect()

        return wrapper
    return decorator

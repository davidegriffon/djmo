# -*- coding: utf-8 -*-
from functools import wraps
from django.db.models.signals import post_save, post_delete
import logging

logger = logging.getLogger(__name__)


class Observer(object):
    """
    Usage:
    self.observer.number_of_objects_created  # if there is only one model
    self.candidate_observer.number_of_objects_created
    self.candidate_observer.number_of_objects_updated
    self.candidate_observer.number_of_objects_deleted
    self.observer[Candidate].number_of_objects_created
    self.candidate_observer.object(self.mario_verdi).is_created
    self.candidate_observer.object(self.mario_verdi).is_updated
    self.candidate_observer.object(self.mario_verdi).is_deleted
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

    def object(self, instance):
        instance.is_created = instance.id in self.objects_created
        instance.is_updated = instance.id in self.objects_updated
        instance.is_deleted = instance.id in self.objects_deleted
        return instance

    def connect(self):
        post_save.connect(self.save_receiver, self.model, dispatch_uid="observe_post_save_model_{}".format(self.model.__name__))
        post_delete.connect(self.delete_receiver, self.model, dispatch_uid="observe_post_delete_model_{}".format(self.model.__name__))

    def disconnect(self):
        post_save.disconnect(self.save_receiver, self.model, dispatch_uid="observe_post_save_model_{}".format(self.model.__name__))
        post_delete.disconnect(self.delete_receiver, self.model, dispatch_uid="observe_post_delete_model_{}".format(self.model.__name__))

    def save_receiver(self, sender, instance=None, created=False, **kwargs):
        if created:
            self.objects_created.append(instance.id)
        else:
            self.objects_updated.append(instance.id)

    def delete_receiver(self, sender, instance=None, **kwargs):
        self.objects_deleted.append(instance.id)


def observe_models(*models):
    def decorator(test_method):
        @wraps(test_method)
        def wrapper(this, *args, **kwargs):
            this.observers = dict()
            # connect signals
            for model in models:
                observer = Observer(model)
                observer.connect()
                this.observers[model] = observer

            # execute test itesef
            test_method(this, *args, **kwargs)

            # disconnect all signals
            for observer in this.observers.values():
                observer.disconnect()

        return wrapper
    return decorator

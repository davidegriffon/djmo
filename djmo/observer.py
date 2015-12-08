from django.db.models.signals import post_save, post_delete
from django.core import serializers


class ModelInstancePatched(object):
    def __init__(self, instance_pk, is_created, is_updated, is_deleted):
        self.pk = instance_pk
        self.is_created = is_created
        self.is_updated = is_updated
        self.is_deleted = is_deleted


class ModelInstanceObserved(object):
    def __init__(self, instance):
        self.model = type(instance)
        self.pk = instance.pk
        self.field_set = {(k, tuple(v)) if isinstance(v, list) else (k, v)
                          for k, v in serializers.serialize('python', [instance])[0]['fields'].items()}

    @property
    def delta(self):
        current_instance = ModelInstanceObserved(self.model.objects.get(pk=self.pk))
        # difference between two sets with - operator
        delta_elements = current_instance.field_set - self.field_set
        # return delta as dictionary
        return {t[0]: t[1] for t in delta_elements}

    def assert_delta_is_equal_to(self, expected_delta_dict):
        expected_delta = {(k, tuple(v)) if isinstance(v, list) else (k, v)
                          for k, v in expected_delta_dict.items()}
        current_instance = ModelInstanceObserved(self.model.objects.get(pk=self.pk))
        # difference between two sets with - operator
        delta = current_instance.field_set - self.field_set
        assert delta == expected_delta

    @property
    def is_created(self):
        return False

    @property
    def is_updated(self):
        return len(self.delta.keys()) != 0

    @property
    def is_deleted(self):
        try:
            self.model.objects.get(pk=self.pk)
        except self.model.DoesNotExist:
            return True
        else:
            return False


class Observer(object):
    """
    An observer observes the model given in init.
    It provides some properties and functions in order to know what's happening in the database.
    """
    def __init__(self, model):
        self.model = model
        self.instances_created = []
        self.instances_updated = []
        self.instances_deleted = []
        self.observed_instances = dict()

    @property
    def number_of_objects_created(self):
        return len(set(self.instances_created))

    @property
    def number_of_objects_updated(self):
        return len(set(self.instances_updated))

    @property
    def number_of_objects_deleted(self):
        return len(set(self.instances_deleted))

    @property
    def nothing_has_changed(self):
        return self.number_of_objects_created + \
            self.number_of_objects_updated + \
            self.number_of_objects_deleted == 0

    def reset(self):
        """reset all internal counters"""
        self.instances_created = []
        self.instances_updated = []
        self.instances_deleted = []

    def observe_instance(self, instance):
        if self.model is not type(instance):
            raise ValueError("instance must be an instance of `{}`".format(self.model))
        self.observed_instances[instance.pk] = ModelInstanceObserved(instance)

    def observe_instances(self, *instances):
        for instance in instances:
            self.observe_instance(instance)

    def monkey_patch_observer(self, test):
        """
        Add to the test method a property to access the observer easily.
        """
        observer_name = "{}_observer".format(self.model.__name__).lower()
        setattr(test, observer_name, self)

    def instance(self, inst):
        """
        :return
            an instance of ModelInstanceObserved if `inst` is observed
            an instance of ModelInstancePatched if `inst` is NOT observed
        """
        instance_pk = inst.pk or getattr(inst, '_old_id', None)
        if instance_pk not in self.observed_instances:
            return ModelInstancePatched(instance_pk=instance_pk,
                                        is_created=instance_pk in self.instances_created,
                                        is_updated=instance_pk in self.instances_updated,
                                        is_deleted=instance_pk in self.instances_deleted)
        else:
            return self.observed_instances[instance_pk]

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
            self.instances_created.append(instance.pk)
        else:
            self.instances_updated.append(instance.pk)

    def delete_receiver(self, sender, instance=None, **kwargs):
        """receiver for delete signal"""
        self.instances_deleted.append(instance.pk)
        instance._old_id = instance.pk

    def assertDelta(self, instance, delta):
        if self.model is not type(instance):
            raise ValueError("instance must be an instance of `{}`".format(self.model))
        if instance.pk not in self.observed_instances:
            raise ValueError('instance must be an observed instance')
        self.observed_instances[instance.pk].assert_delta_is_equal_to(delta)

    def assertModelIsUntouched(self):
        assert self.number_of_objects_created == 0
        assert self.number_of_objects_updated == 0
        assert self.number_of_objects_deleted == 0

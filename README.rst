Django Model Observer
---------------------

Note: beta version

Simple Django plugin that provides some goodies useful to know what's happening in your database.
It can be useful in tests, for example when you use one function with side effects.
With observe_models decorator you attach observers you want, and use later to see what happened in your DB.

Example:

.. code:: python

    @observe_models(YourModel)
    def test_function_with_side_effects(self):
        # this function has some side effects you want to test
        rest_call(*some_arguments)
        # `observe_models` decorator attach to the test the dictionary `observers`
        # use self.observers[YourModel] to obtain YourModel's observer
        self.observers[YourModel].number_of_objects_created
        self.observers[YourModel].number_of_objects_updated
        self.observers[YourModel].number_of_objects_deleted
        # etc..

Other example:

.. code:: python

    @observe_models(User)
    def test_foo(self):
        mario = User.objects.create(username='mario', password='foobar123')
        wario = User.objects.get(username='wario')
        wario.email = 'wario@example.com'
        wario.save()

        # then you can use User's observer
        self.observers[User].number_of_objects_created # returns 1 (mario)
        self.observers[User].number_of_objects_updated # returns 1 (wario)
        self.observers[User].number_of_objects_deleted # returns 0

        # you can use `instance(model_instance)` method to see what happened to the instance given
        self.observers[User].instance(mario).is_created # returns True
        self.observers[User].instance(mario).is_updated # returns False
        self.observers[User].instance(mario).is_deleted # returns False

        # an alternative manner to access the observer: the property `modelname_observer` lowercased
        self.user_observer.number_of_objects_created # returns 1 (mario)

        # or, if you have only one model observed
        self.observer.number_of_objects_created # returns 1 (mario)


You can attach more observers:

.. code:: python

    @observe_models(User, Group, Foo)
    def test_bar(self):
        # the access observer with
        self.observers[User]
        # or
        self.group_observer
        # etc

You can also observe specific instances:

.. code:: python

    @observe_models(SoccerPlayer)
    def test_instance_delta(self):
        mario_rossi = SoccerPlayer.objects.get(last_name='Rossi')
        # use method `observe_instances` to start observing an instance
        self.observers[SoccerPlayer].observe_instances(mario_rossi)

        # some operation on Mario Rossi
        mario_rossi.last_name = "Arancioni"
        mario_rossi.save()

        # then you can see what happened to the instance since now
        # `delta` property return a dict
        self.observers[SoccerPlayer].instance(mario_rossi).delta # return {'last_name': 'Arancioni'}

        # you can also use `assertDelta` to check what's changed
        self.observers[SoccerPlayer].assertDelta(mario_rossi, {'last_name': 'Arancioni'})

        # other useful properties
        self.observers[SoccerPlayer].instance(mario_rossi).is_updated  # returns True
        self.observers[SoccerPlayer].instance(mario_rossi).is_deleted  # returns False


## Tests

To run tests go in the `tests` folder, then `export DJANGO_SETTINGS_MODULE=project_for_tests.settings` and `python manage.py test`

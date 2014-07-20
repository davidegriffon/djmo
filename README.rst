dj-model-observer
-----------------

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

        # then you can test using observer, using for example
        self.observers[User].number_of_objects_created # return 1 (mario)
        self.observers[User].number_of_objects_updated # return 1 (wario)
        self.observers[User].number_of_objects_deleted # return 0
        self.observers[User].nothing_has_changed # return False

        # you can use `object(model_instance)` method to see what happened to the instance given
        self.observers[User].object(mario).is_created # return True
        self.observers[User].object(mario).is_updated # return False
        self.observers[User].object(mario).is_deleted # return False
        self.observers[User].object(mario).is_untouched # return False

        # an alternative manner to access the observer: the property `modelname_observer` lowercased
        self.user_observer.number_of_objects_created # return 1 (mario)

        # or, if you have only one model observed
        self.observer.number_of_objects_created # return 1 (mario)

    # you can attach more observers:
    @observe_models(User, Group, Foo)
    def test_bar(self):
        # the access observer with
        self.observers[User]
        # or
        self.group_observer
        # etc

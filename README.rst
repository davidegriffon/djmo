dj-model-observer
-----------------

note: alpha version

Simple Django plugin that provides some goodies useful to know what's happening in your database.

Example usage:

.. code:: python

    @observe_models(User)  # decorator used to observe the model User
    def test_foo(self):
        mario = User.objects.create(username='mario', password='foobar123')
        wario = User.objects.get(username='wario')
        wario.email = 'wario@example.com'
        wario.save()
        # then you can test using observer, using for example
        self.observers[User].number_of_objects_created # return 1 (mario)
        self.observers[User].number_of_objects_updated # return 1 (wario)
        self.observers[User].number_of_objects_deleted # return 0
        self.observers[User].object(mario).is_created # return True
        self.observers[User].object(mario).is_updated # return False
        self.observers[User].object(mario).is_deleted # return False



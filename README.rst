dj-model-observer
-----------------

note: alpha version

This simple django plugin can be useful when you want to monitor what it's saved in your database in your tests.

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
        self.observers[User].number_of_objects_delete # return 0

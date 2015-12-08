from setuptools import setup

setup(
    name='djmo',
    description='Django Model Observer',
    version='0.0.1',
    url='https://github.com/griffosx/dj-model-observer',
    author='Davide Giuseppe Griffon',
    author_email='davide.griffon@gmail.com',
    license='MIT',
    packages=['djmo'],
    install_requires=['django'],
    keywords='django test utility',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Testing',
    ],
    zip_safe=False,
)

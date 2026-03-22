from setuptools import setup, find_packages

setup(
    name='8bitify',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'click',
        'pydub',
        'numpy',
        'iterfzf',
        'scipy',
        'audioop-lts',
        'librosa',
    ],
    entry_points={
        'console_scripts': [
            '8bitify=bitify.cli:main',
        ],
    },
)

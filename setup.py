from distutils.core import setup

setup(include_package_data=True,
      data_files=[('emoji_extractor', ['emoji_extractor/data/big_regex.pkl', 'emoji_extractor/data/possible_emoji.pkl'])],
    name = 'emoji_extractor',
    packages = ['emoji_extractor'],
    version = '1.0.8',
    description = 'Extract, detect and count emoji',
    author='Alexander Robertson',
    author_email='alexander.robertson@ed.ac.uk',
    url='https://github.com/alexanderrobertson/emoji-extractor',
    classifiers=['Programming Language :: Python :: 3',
    			'Topic :: Text Processing :: General',
    			'License :: OSI Approved :: MIT License',


    ]
)
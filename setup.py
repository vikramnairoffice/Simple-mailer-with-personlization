from setuptools import setup, find_packages

# Read requirements from requirements.txt if it exists
def parse_requirements():
    """Parse requirements from requirements.txt file."""
    try:
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        # Fallback to hardcoded requirements
        return [
            'gradio>=3.0.0',
            'reportlab>=3.6.0',
            'pymupdf>=1.20.0',
            'faker>=15.0.0',
            'google-auth-oauthlib>=0.8.0',
            'google-api-python-client>=2.70.0',
            'requests>=2.25.0',
            'beautifulsoup4>=4.9.0',
            'Pillow>=8.0.0'
        ]

# Read long description from README
def get_long_description():
    """Get long description from README.md."""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Python email marketing application with personalized invoice generation and GMass deliverability testing."

setup(
    name='simple-mailer-personalized',
    version='1.0.0',
    author='Vikram Nair',
    author_email='vikramnairoffice@gmail.com',
    description='Python email marketing application with personalized invoice generation and GMass deliverability testing',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/vikramnairoffice/Simple-mailer-with-personlization',
    packages=find_packages(),
    py_modules=[
        'ui',
        'mailer',
        'invoice',
        'content',
        'sender_names'
    ],
    install_requires=parse_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.10.0',
            'black>=21.0.0',
            'flake8>=3.8.0'
        ],
        'colab': [
            'ipython>=7.0.0',
            'jupyter>=1.0.0'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications :: Email',
        'Topic :: Office/Business :: Financial :: Accounting',
    ],
    python_requires='>=3.7',
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.json'],
    },
    entry_points={
        'console_scripts': [
            'simple-mailer=ui:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/vikramnairoffice/Simple-mailer-with-personlization/issues',
        'Source': 'https://github.com/vikramnairoffice/Simple-mailer-with-personlization',
        'Documentation': 'https://github.com/vikramnairoffice/Simple-mailer-with-personlization/blob/master/README.md',
    },
)
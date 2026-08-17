"""Setup configuration for Smart File Organizer."""

from setuptools import setup, find_packages

setup(
    name='smart-file-organizer',
    version='1.0.0',
    description='A CLI tool to scan, organize, deduplicate files and generate reports.',
    author='Jay',
    python_requires='>=3.10',
    packages=find_packages(),
    install_requires=[
        'click>=8.1.0',
        'pandas>=2.0.0',
        'Pillow>=10.0.0',
        'PyYAML>=6.0',
    ],
    extras_require={
        'dev': ['pytest>=7.0.0'],
    },
    entry_points={
        'console_scripts': [
            'smart-organizer=smart_organizer.cli:cli',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)

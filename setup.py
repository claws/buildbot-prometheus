
import os
import re

from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import setup


install_reqs = parse_requirements("requirements.txt", session=PipSession())
requires = [str(ir.req) for ir in install_reqs]


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*['\"](\d\d\.\d+.\d+)['\"]")
    init_file = os.path.join(
        os.path.dirname(__file__), 'buildbot_prometheus', '__init__.py')
    with open(init_file) as f:
        for line in f:
            match = regexp.match(line)
            if match:
                return match.group(1)
        else:
            raise RuntimeError(
                'Cannot find __version__ in buildbot_prometheus/__init__.py')


version = read_version()


if __name__ == "__main__":

    setup(
        name="buildbot_prometheus",
        version=version,
        author="Chris Laws",
        author_email="clawsicus@gmail.com",
        description="A Prometheus exporter for Buildbot",
        long_description="",
        license="MIT",
        keywords=["buildbot", "prometheus", "monitoring", "metrics"],
        url="https://github.com/claws/buildbot-prometheus",
        packages=["buildbot_prometheus"],
        install_requires=requires,
        entry_points = {
            'buildbot.reporters': 'Prometheus = buildbot_prometheus:Prometheus'},
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.5",
            "Topic :: System :: Monitoring"])

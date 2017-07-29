#!/usr/bin/env bash
#
# Perform a crude check on the generated distribution artefact.
# Creates a virtual environment, installs buildbot_prometheus,
# creates a master and starts it, checks the Prometheus service,
# then finally stop the master and remove the temporary artefacts.
#
# Example:
#    $ ./test.bash ../dist/buildbot_prometheus-17.7.1-py2.py3-none-any.whl
#

PYTHON_TARGET="3"  # valid options are "3" or 2"

if [ -z "$1" ]; then
  echo "usage: $0 buildbot_prometheus-YY.MM.MICRO-py2.py3-none-any.whl"
  exit
fi

RELEASE_ARCHIVE="$1"

echo "Release archive: $RELEASE_ARCHIVE"

echo "Removing any old artefacts"
rm -rf bbpvenv

echo "Creating test virtual environment using Python $PYTHON_TARGET"
if [ $PYTHON_TARGET == "3" ]; then
    python3 -m venv bbpvenv
else
    python2.7 -m virtualenv bbpvenv
fi

echo "Entering test virtual environment"
source bbpvenv/bin/activate

echo "Upgrading pip"
pip install pip --upgrade

# Install the bundle to get the web components.
echo "Installing buildbot[bundle]"
pip install buildbot[bundle]

echo "Installing $RELEASE_ARCHIVE"
pip install $RELEASE_ARCHIVE

echo "Creating a buildbot master"
buildbot create-master master
rm -f master/master.cfg.sample
cp master.cfg.test master/master.cfg
buildbot start master
sleep 2

echo "Checking buildbot Prometheus service"
curl -s localhost:9100/metrics | grep -v "#" | sort

echo "Stopping a buildbot master"
buildbot stop master

rm -rf master

echo "Exiting test virtual environment"
deactivate

echo "Removing test virtual environment"
rm -rf bbpvenv


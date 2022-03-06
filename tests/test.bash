#!/usr/bin/env bash
#
# Perform a crude check on the generated distribution artefact.
# Creates a virtual environment, installs buildbot_prometheus,
# creates a buildbot master and starts it, checks the Prometheus
# service, then finally stops the master and removes the temporary
# artefacts.
#
# Example:
#    $ ./test.bash ../dist/buildbot_prometheus-22.0.0--py3-none-any.whl
#

PYTHON_TARGET="3.9"

if [ -z "$1" ]; then
  echo "usage: $0 buildbot_prometheus-YY.MM.MICRO-py3-none-any.whl"
  exit
fi

RELEASE_ARCHIVE="$1"

echo "Release archive: $RELEASE_ARCHIVE"

echo "Removing any old artefacts"
rm -rf bbpvenv

echo "Creating test virtual environment using Python $PYTHON_TARGET"
python$PYTHON_TARGET -m venv venv --prompt bbpvenv

echo "Entering test virtual environment"
source venv/bin/activate

echo "Upgrading pip"
pip install pip --upgrade
# install wheel package to simplify third party package installation
pip install wheel

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

if [ $? -eq 0 ]; then
  sleep 2

  echo "Checking buildbot Prometheus service"
  curl -s localhost:9100/metrics | grep -v "#" | sort

  echo "Stopping a buildbot master"
  buildbot stop master
else
  echo "Error starting buildbot master"
  echo ""
  echo "Printing 'master/twistd.log' which might explain why..."
  cat master/twistd.log
  echo ""
fi

sleep 1
echo "Removing the buildbot master directory"
rm -rf master

echo "Exiting test virtual environment"
deactivate

echo "Removing test virtual environment"
rm -rf venv

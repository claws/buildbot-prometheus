#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "usage: $0 buildbot_prometheus-YY.MM.MICRO.tar.gz"
  exit
fi

RELEASE_ARCHIVE="$1"
RELEASE_DIR=`echo $RELEASE_ARCHIVE | sed -e "s/\.tar\.gz//g"`

echo "Release archive: $RELEASE_ARCHIVE"
echo "Release directory: $RELEASE_DIR"

echo "Removing any old artefacts"
rm -rf $RELEASE_DIR
rm -rf bbpvenv

echo "Creating test virtual environment"
python2.7 -m virtualenv bbpvenv

echo "Entering test virtual environment"
source bbpvenv/bin/activate

echo "Upgrading pip"
pip install pip --upgrade

echo "Installing $RELEASE_ARCHIVE"
tar xf $RELEASE_ARCHIVE
cd $RELEASE_DIR
pip install .
cd ..

echo "Creating a new buildbot master"
buildbot create-master master
rm -f master/master.cfg.sample
cp master.cfg.test master/master.cfg
buildbot start master
sleep 2
curl -s localhost:9100/metrics | grep -v "#" | sort
buildbot stop master

rm -rf master

echo "Exiting test virtual environment"
deactivate

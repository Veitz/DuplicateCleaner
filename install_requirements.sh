#!/bin/bash

set -e

echo "System-Paketlisten aktualisieren..."
sudo apt update

echo "Python3 und pip3 installieren..."
sudo apt install -y python3 python3-pip

#echo "Python-Abhängigkeiten installieren..."
#pip3 install --user send2trash


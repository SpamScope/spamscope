#!/bin/sh

FAUP_PATH=/tmp/faup

git clone https://github.com/stricaud/faup.git ${FAUP_PATH}
mkdir -p ${FAUP_PATH}/build
cd ${FAUP_PATH}/build
cmake .. 
make 
sudo make install
echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf.d/faup.conf
sudo ldconfig 
ldd /usr/local/bin/faup

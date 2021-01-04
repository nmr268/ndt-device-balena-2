cvVersion="4.1.0"
tmpDir="/tmp/opencv-install"
threads=$(nproc --all)

apt-get -y install cmake
apt-get -y install python-dev python-numpy
apt-get -y install gcc g++

apt-get -y install git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev

apt install -y python-pip

pip install -r requirements.txt

git clone https://github.com/opencv/opencv.git $tmpDir/opencv
cd $tmpDir/opencv
git checkout $cvVersion
cd ..
 
git clone https://github.com/opencv/opencv_contrib.git $tmpDir/opencv_contrib
cd /$tmpDir/opencv_contrib
git checkout $cvVersion
cd ..

cd $tmpDir/opencv
mkdir build
cd build

cmake ../

make -j$threads

make install

curl -sL -o libjpeg-turbo.tar.gz "https://sourceforge.net/projects/libjpeg-turbo/files/1.5.1/libjpeg-turbo-1.5.1.tar.gz/download"
tar xzf libjpeg-turbo.tar.gz
mv libjpeg-turbo-* libjpeg-turbo-build
cd libjpeg-turbo-build
./configure --enable-static=no --prefix=/tmp/libjpeg-turbo-build
make install >/dev/null || make install
cd ..
rm -rf libjpeg-turbo-build

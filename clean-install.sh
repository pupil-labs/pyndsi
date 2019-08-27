rm -rf build
rm -rf ndsi.egg-info
rm -rf ndsi/ndsi.egg-info
rm ndsi/*.cpp
rm ndsi/*.so

pip3 install -e . --user --force

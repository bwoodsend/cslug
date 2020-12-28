#!/bin/bash
set -e -x

# This is to be run by Docker inside a Docker image.
# You can test it locally on a Linux machine by installing Docker and running from this
# repo's root:
# $ docker run -e PLAT=manylinux1_x86_64 -v `pwd`:/io quay.io/pypa/manylinux1_x86_64 /io/scripts/build-manylinux-wheels.sh

# The -e just defines an environment variable PLAT=[docker name] inside the Docker:
# auditwheel can't detect the Docker name automatically.

# The -v gives a directory alias for passing files in and out of the Docker.
# (/io is arbitrary). E.g the setup.py script can be accessed in the Docker via
# /io/setup.py quay.io/pypa/manylinux1_x86_64 is the full Docker image name. Docker
# downloads it automatically.

# The last argument is a shell command that the Docker will execute. Filenames must be
# from the Docker's perspective.

# Wheels are initially generated as you would usually, but put in a temp directory temp-wheels.
# The pip-cache is optional but can speed up local builds having a real permanent pip-cache dir.

# Clean out any old existing wheels.
mkdir -p /io/temp-wheels/
find /io/temp-wheels/ -type f -delete

for PYBIN in /opt/python/cp38*/bin; do
    cd /io/
    $PYBIN/pip install wheel
    $PYBIN/pip wheel --no-deps --find-links=/cslug-dist/ -w /io/temp-wheels .
done

"$PYBIN/pip" install -q auditwheel

# Wheels aren't considered manylinux unless they have been through
# auditwheel. Audited wheels go in /io/dist/.
mkdir -p /io/dist/

for whl in /io/dist/*.whl; do
    auditwheel repair "$whl" --plat=manylinux1_i686
done

#!/usr/bin/env bash

# RUN: bash %s %T/broken_build
# RUN: cd %T/broken_build; %{intercept-build} --cdb wrapper.json --override-compiler ./run.sh
# RUN: cd %T/broken_build; cdb_diff wrapper.json expected.json
#
# when library preload disabled, it falls back to use compiler wrapper
#
# RUN: cd %T/broken_build; %{intercept-build} --cdb preload.json ./run.sh
# RUN: cd %T/broken_build; cdb_diff preload.json expected.json

set -o errexit
set -o nounset
set -o xtrace

# the test creates a subdirectory inside output dir.
#
# ${root_dir}
# ├── run.sh
# ├── expected.json
# └── src
#    └── broken.c

root_dir=$1
mkdir -p "${root_dir}/src"

cp "${test_input_dir}/compile_error.c" "${root_dir}/src/broken.c"

build_file="${root_dir}/run.sh"
cat >> ${build_file} << EOF
#!/usr/bin/env bash

set -o nounset
set -o xtrace

"\$CC" -c -o src/broken.o -Dver=1 src/broken.c;
"\$CXX" -c -o src/broken.o -Dver=2 src/broken.c;

cd src
"\$CC" -c -o broken.o -Dver=3 broken.c;
"\$CXX" -c -o broken.o -Dver=4 broken.c;

true;
EOF
chmod +x ${build_file}

cat >> "${root_dir}/expected.json" << EOF
[
{
  "command": "cc -c -o src/broken.o -Dver=1 src/broken.c",
  "directory": "${root_dir}",
  "file": "src/broken.c"
}
,
{
  "command": "c++ -c -o src/broken.o -Dver=2 src/broken.c",
  "directory": "${root_dir}",
  "file": "src/broken.c"
}
,
{
  "command": "cc -c -o broken.o -Dver=3 broken.c",
  "directory": "${root_dir}/src",
  "file": "broken.c"
}
,
{
  "command": "c++ -c -o broken.o -Dver=4 broken.c",
  "directory": "${root_dir}/src",
  "file": "broken.c"
}
]
EOF

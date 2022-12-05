#!/bin/bash

set -e

. /opt/ros/"$ROS_DISTRO"/setup.sh
. /ros2_caret_ws/install/local_setup.sh

cd /work

python3 caret2influxdb.py /trace_data --bucket_name "${bucket_name}"

exec "$@"

FROM osrf/ros:humble-desktop

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        locales=2.35-0ubuntu3.1 \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

# ADD "https://www.random.org/sequences/?min=1&max=52&col=1&format=plain&rnd=new" /dev/null
# Build CARET (Humble)
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# hadolint ignore=DL3003
RUN git clone https://github.com/tier4/caret.git ros2_caret_ws && \
    cd ros2_caret_ws && \
    mkdir src && \
    vcs import src < caret.repos && \
    . /opt/ros/"$ROS_DISTRO"/setup.sh && \
    ./setup_caret.sh -c && \
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF

RUN pip3 install --no-cache-dir influxdb-client

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

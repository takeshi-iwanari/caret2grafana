![image](https://user-images.githubusercontent.com/11009876/205484514-2ee95c3c-b371-4d95-ab15-e5bf84523dab.png)

# caret2grafana

## About

- Create InfluxDB from CARET trace data
- Display dashboards in Grafana using the created database

## (optional) Docker containers

### CARET

```sh
docker image build -t caret/caret2influxdb ./docker
```

### InfluxDB

```sh
mkdir ./influxdb
mkdir ./influxdb/config
mkdir ./influxdb/data

docker run --rm -d -p 8086:8086 \
  -v $PWD/influxdb/data:/var/lib/influxdb2 \
  -v $PWD/influxdb/config:/etc/influxdb2 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=my-user \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=my-password \
  -e DOCKER_INFLUXDB_INIT_ORG=my-org \
  -e DOCKER_INFLUXDB_INIT_BUCKET=my-bucket \
  -e DOCKER_INFLUXDB_INIT_RETENTION=1w \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \
  influxdb:2.4.0
```

- Access http://localhost:8086/signin to explorer your database
  - Username: my-user
  - Password: my-password

### Grafana

```sh
mkdir ./grafana

docker run --name grafana \
  --user `id -u` \
  -v $PWD/grafana:/var/lib/grafana \
  --net host \
  -p 3000:3000 \
  -d --rm grafana/grafana
```

- Access http://localhost:3000/ to show your dashboards
  - Username: admin
  - Password: admin

## Steps

1. Setup InfluxDB server
  - Use the above Docker container in this explanation

2. Store CARET trace data into InfluxDB
  - You have two options:
  - a. Use the above Docker container

    ```sh
    work_dir=`pwd`
    trace_data=~/.ros/tracing/session-yyyymmdd-hhmmss
    docker run -it --rm \
      --net host \
      -v ${work_dir}:/work \
      -v ${trace_data}:/trace_data \
      -v /etc/localtime:/etc/localtime:ro \
      -e measurement_name=`basename ${trace_data}` \
      caret/caret2influxdb
    ```

  - b. Run the script locally

    ```sh
    python3 caret2influxdb.py ~/.ros/tracing/session-yyyymmdd-hhmmss
    ```

3. Setup Grafana
  - Login to Grafana
  - Configure datasource
    - `Configuration` -> `Data sources` -> `Add data source`
    - Select `InfluxDB`, and process the following settings, then click `Save & Test`
      - Query Language: Flux
      - URL: http://localhost:8086
      - User: my-user
      - Password: my-password
      - my-user: my-org
      - Token: my-super-secret-auth-token
  - Configure dashboards
    - `Dashboards` -> `Browse` -> `New` -> `Import`
    - `Upload JSON file`
      - Select  `./dashboard/single_node.json`
      - Click `Import`

## Scheme

### Node Analysis

- bucket: "autoware" or product name
- measurement: LTTng trace data name (some name for a experiment/measurement)
- tag
  - component_name
  - node_name
  - callback_name
- field
  - frequency
  - period
  - latency
- time: datetime of tracepoint

### History Information

- bucket: "history"
- measurement: "autoware" or product name
- tag
  - measurement info: tag
  - measurement info: release data
  - measurement info: environment (sim, car, etc/)
  - component_name
  - node_name
  - callback_name
  - type: avg, median, min, mx, min_90%, max_90%, min_95%, max_95%
- field
  - frequency
  - period
  - latency
- time: datetime of measurement

"""
Script to convert CARET to InfluxDB
"""
from __future__ import annotations
from typing import Optional
import sys
import os
from pathlib import Path
import argparse
import logging
import numpy as np
import pandas as pd
from datetime import datetime

import influxdb_client

from caret_analyze import Architecture, Application, Lttng
from caret_analyze.runtime.callback import CallbackBase
from caret_analyze.plot import Plot

import utils

_logger: logging.Logger = None

def create_bucket(url, token, org, bucket_name: str):
    with influxdb_client.InfluxDBClient(url=url, token=token) as client:
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets().buckets
        my_buckets = [bucket for bucket in buckets if bucket.name==bucket_name]
        _ = [buckets_api.delete_bucket(my_bucket) for my_bucket in my_buckets]
        _ = buckets_api.create_bucket(bucket_name=bucket_name, org=org)


def write_df(url, token, org, bucket_name, measurement_name, df, component_name, node_name, callback_name):
    with influxdb_client.InfluxDBClient(url=url, token=token, org=org) as client:
        point_settings = influxdb_client.client.write_api.PointSettings()
        point_settings.add_default_tag('component_name', component_name)
        point_settings.add_default_tag('node_name', node_name)
        point_settings.add_default_tag('callback_name', callback_name)
        write_api = client.write_api(write_options=influxdb_client.client.write_api.SYNCHRONOUS, point_settings=point_settings)
        write_api.write(bucket=bucket_name, record=df, data_frame_measurement_name=measurement_name)


def write_df_history(url, token, org, bucket_name, measurement_datetime, measurement_name, df: pd.DataFrame, component_name, node_name, callback_name):
    metrics = df.columns[0]
    df = df[1:-2]
    if len(df) < 2:
        return
    with influxdb_client.InfluxDBClient(url=url, token=token, org=org) as client:
        point_settings = influxdb_client.client.write_api.PointSettings()
        write_api = client.write_api(write_options=influxdb_client.client.write_api.SYNCHRONOUS, point_settings=point_settings)

        p = influxdb_client.Point('product_a')\
            .tag('relese_tag', 'v1.0.0')\
            .tag('relese_date', '2022/12/05')\
            .tag('environment', 'sim')\
            .tag('measurement_name', measurement_name)\
            .tag('component_name', component_name)\
            .tag('node_name', node_name)\
            .tag('callback_name', callback_name)\
            .tag('type', 'avg')\
            .time(measurement_datetime)

        write_api.write(bucket=bucket_name, record=p.field(metrics, float(df.mean())).tag('type', 'avg'))
        write_api.write(bucket=bucket_name, record=p.field(metrics, float(df.median())).tag('type', 'median'))
        write_api.write(bucket=bucket_name, record=p.field(metrics, float(df.min())).tag('type', 'min'))
        write_api.write(bucket=bucket_name, record=p.field(metrics, float(df.max())).tag('type', 'max'))


def make_callback_name(callback: CallbackBase) -> str:
    """Make callback name to be displayed"""
    callback_type = callback.callback_type.type_name
    if 'timer' in callback_type:
        period_ms = callback.timer.period_ns * 1e-6
        if period_ms.is_integer():
            displayname = f'Timer_{int(period_ms)}ms'
        else:
            displayname = f'Timer_{period_ms:.3f}ms'
    elif 'subscription' in callback_type:
        displayname = 'Sub_' + str(callback.subscribe_topic_name)
    return displayname


def convert(app: Application, url, token, org, bucket_name, measurement_name, measurement_datetime):
    """Analyze nodes"""
    global _logger
    _logger.info('<<< Convert: Start >>>')

    create_bucket(url, token, org, bucket_name)
    create_bucket(url, token, org, 'history')

    all_metrics_dict = {'Frequency [Hz]': Plot.create_callback_frequency_plot,
                        'Period [ms]': Plot.create_callback_period_plot,
                        'Latency [ms]': Plot.create_callback_latency_plot}

    for node in app.nodes:
        node_name = node.node_name
        component_name = node_name.lstrip('/').split('/')[0]
        for callback in node.callbacks:
            callback_name = make_callback_name(callback)
            for metrics, method in all_metrics_dict.items():
                try:
                    plot = method([callback])
                    df = plot.to_dataframe()
                except:
                    print(f'Not called: {node_name}: {callback_name}')
                    continue
                multi_index_name = df.columns[0][0]
                df = df[multi_index_name]    # collapse multi index structure
                # df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
                df = df.set_index(df.columns[0])
                df.columns = [metrics]
                write_df(url, token, org, bucket_name, measurement_name, df, component_name, node_name, callback_name)
                write_df_history(url, token, org, 'history', measurement_datetime, measurement_name, df, component_name, node_name, callback_name)

    _logger.info('<<< Convert: Finish >>>')


def parse_arg():
    """Parse arguments"""
    parser = argparse.ArgumentParser(
                description='Script to convert CARET to InfluxDBs')
    parser.add_argument('trace_data', nargs=1, type=str)
    parser.add_argument('-s', '--start_point', type=float, default=0.0,
                        help='Start point[sec] to load trace data')
    parser.add_argument('-d', '--duration', type=float, default=0.0,
                        help='Duration[sec] to load trace data')
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Overwrite report directory')
    parser.add_argument('--url', type=str, default='http://localhost:8086',
                        help='InfluxDB URL')
    parser.add_argument('--token', type=str, default='my-super-secret-auth-token',
                        help='InfluxDB Token')
    parser.add_argument('--org', type=str, default='my-org',
                        help='InfluxDB Organization')
    parser.add_argument('--bucket_name', type=str, default=None,
                        help='InfluxDB Bucket Name')
    parser.add_argument('--measurement_name', type=str, default=None,
                        help='InfluxDB measurement Name')
    parser.add_argument('--measurement_datetime', type=str, default=datetime.now(),
                        help='InfluxDB measurement datetime')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    args = parser.parse_args()
    return args


def main():
    """Main function"""
    global _logger
    args = parse_arg()
    _logger = utils.create_logger(__name__, logging.DEBUG if args.verbose else logging.INFO)

    _logger.debug(f'trace_data: {args.trace_data[0]}')
    _logger.debug(f'start_point: {args.start_point}, duration: {args.duration}')
    _logger.debug(f'url: {args.url}, token: {args.token}, org: {args.org}')

    bucket_name = args.bucket_name if args.bucket_name is not None else 'caret'
    measurement_name = args.measurement_name if args.measurement_name is not None \
        else args.trace_data[0].rstrip('/').split('/')[-1]
    _logger.debug(f'bucket_name: {bucket_name}, measurement_name: {measurement_name}')

    measurement_datetime = int(args.measurement_datetime.timestamp() * 1e9)
    _logger.debug(f'measurement_datetime: {args.measurement_datetime}, {measurement_datetime}')

    lttng = utils.read_trace_data(args.trace_data[0], args.start_point, args.duration, False)
    arch = Architecture('lttng', str(args.trace_data[0]))
    app = Application(arch, lttng)

    convert(app, args.url, args.token, args.org, bucket_name, measurement_name, measurement_datetime)


if __name__ == '__main__':
    main()

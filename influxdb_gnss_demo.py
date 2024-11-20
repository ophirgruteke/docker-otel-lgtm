from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import (
    CallbackOptions,
    Observation,
    get_meter_provider,
    set_meter_provider,
)
from typing import Iterable
from loguru import logger
import time

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
import pandas as pd
from pynmea2 import parse

exporter = OTLPMetricExporter(endpoint="http://localhost:4317")
metric_reader = PeriodicExportingMetricReader(exporter, export_interval_millis=1000)
provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter(__name__)

# Variables to hold the latest metric values
latest_latitude = 0.0
latest_longitude = 0.0
latest_signal_strength = 0

# Define observable gauges with callbacks
def latitude_callback(options):
    yield Observation(latest_latitude, {})

def longitude_callback(options):
    yield Observation(latest_longitude, {})

def signal_strength_callback(options):
    yield Observation(latest_signal_strength, {})

latitude_metric = meter.create_observable_gauge(
    "gnss_latitude",
    callbacks=[latitude_callback],
    description="Latitude of GNSS",
)

longitude_metric = meter.create_observable_gauge(
    "gnss_longitude",
    callbacks=[longitude_callback],
    description="Longitude of GNSS",
)

signal_strength_metric = meter.create_observable_gauge(
    "gnss_signal_strength",
    callbacks=[signal_strength_callback],
    description="Signal strength of satellite",
)

# Load CSV data
df = pd.read_csv("gnss.csv")

# Function to parse NMEA sentences and extract key metrics
def extract_metrics_from_nmea(nmea_sentence):
    global latest_latitude, latest_longitude, latest_signal_strength
    try:
        msg = parse(nmea_sentence)
        # Extract data based on message type, e.g., GGA or GSV for GNSS metrics
        if msg.sentence_type == 'GGA':  # GPS Fix Data
            latest_latitude = msg.latitude
            latest_longitude = msg.longitude
            print(f"Updated latitude: {latest_latitude}, longitude: {latest_longitude}")
        elif msg.sentence_type == 'GSV':  # Satellites in View
            latest_signal_strength = msg.snr
            print(f"Updated signal strength: {latest_signal_strength}")
    except Exception as e:
        print(f"Error parsing NMEA sentence: {e}")

# Iterate through rows and extract metrics for each NMEA sentence
for index, row in df.iterrows():
    nmea_sentence = row['nmea_sentence']
    logger.info(f"Processing NMEA sentence: {nmea_sentence}")
    extract_metrics_from_nmea(nmea_sentence)
    time.sleep(1)  # Add a delay to simulate periodic updates

# # Keep the script running to allow the exporter to send data
# logger.info("Exporter is running...")
# while True:
#     time.sleep(60)


# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# exporter = OTLPMetricExporter(insecure=True)
# reader = PeriodicExportingMetricReader(exporter)
# provider = MeterProvider(metric_readers=[reader])
# set_meter_provider(provider)


# def observable_counter_func(options: CallbackOptions) -> Iterable[Observation]:
#     yield Observation(1, {})


# def observable_up_down_counter_func(
#     options: CallbackOptions,
# ) -> Iterable[Observation]:
#     yield Observation(-10, {})


# def observable_gauge_func(options: CallbackOptions) -> Iterable[Observation]:
#     yield Observation(9, {})


# meter = get_meter_provider().get_meter("getting-started", "0.1.2")

# # Counter
# counter = meter.create_counter("counter")
# counter.add(1)

# # Async Counter
# observable_counter = meter.create_observable_counter(
#     "observable_counter",
#     [observable_counter_func],
# )

# # UpDownCounter
# updown_counter = meter.create_up_down_counter("updown_counter")
# updown_counter.add(1)
# updown_counter.add(-5)

# # Async UpDownCounter
# observable_updown_counter = meter.create_observable_up_down_counter(
#     "observable_updown_counter", [observable_up_down_counter_func]
# )

# # Histogram
# histogram = meter.create_histogram("histogram")
# histogram.record(99.9)

# # Async Gauge
# gauge = meter.create_observable_gauge("gauge", [observable_gauge_func])
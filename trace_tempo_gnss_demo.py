import pandas as pd
import pynmea2
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import serial

# Step 1: Set up OpenTelemetry tracing
trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({"service.name": "gps-data-receiver"}))
)
tracer = trace.get_tracer(__name__)
span_exporter = OTLPSpanExporter(endpoint="172.25.14.68:4317", insecure=True)  # Replace with your endpoint
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(span_exporter))

# Step 2: Load CSV with generated NMEA sentences
csv_path = 'gnss.csv'  # Path to the generated CSV file
nmea_df = pd.read_csv(csv_path)

# Step 3: Process each NMEA sentence from the CSV
for _, row in nmea_df.iterrows():
    line = row['nmea_sentence']
    timestamp = row['timestamp']
    
    try:
        nmea_sentence = pynmea2.parse(line)

        # Start a span for processing each NMEA sentence
        with tracer.start_as_current_span("process_nmea_sentence") as span:
            # Set attributes to provide detailed context for the span
            span.set_attribute("nmea_type", type(nmea_sentence).__name__)
            span.set_attribute("raw_sentence", line)
            span.set_attribute("timestamp", timestamp)

            # Log an event in the span for additional context
            span.add_event(
                "received_nmea_sentence",
                {
                    "raw_sentence": line,
                    "timestamp": timestamp
                }
            )

            # Example: Extract and set GPS-specific attributes if the sentence is GGA
            if isinstance(nmea_sentence, pynmea2.GGA):
                span.set_attribute("latitude", nmea_sentence.latitude)
                span.set_attribute("longitude", nmea_sentence.longitude)
                span.set_attribute("altitude", nmea_sentence.altitude)
                span.set_attribute("num_satellites", nmea_sentence.num_sats)

                # Log an event for location data
                span.add_event(
                    "parsed_gps_data",
                    {
                        "latitude": nmea_sentence.latitude,
                        "longitude": nmea_sentence.longitude,
                        "altitude": nmea_sentence.altitude,
                        "num_satellites": nmea_sentence.num_sats
                    }
                )

    except pynmea2.ParseError as e:
        print(f"Failed to parse NMEA sentence: {line}, error: {e}")
        continue

print("GPS NMEA data has been processed and exported.")

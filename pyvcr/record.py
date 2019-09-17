import logging
import time
import datetime

import requests

LOGGER = logging.getLogger(__name__)
CHUNK_SIZE = 1024


def record_stream(stream_url, output_file, duration):
    """Record `stream_url` in `output_file` for `duration` seconds.

    :param stream_url: `string` URL of the stream.
    :param output_file: `string` path to the output file.
    :param duration: `int` duration in seconds.
    """
    start_time = time.time()
    written_bytes = 0

    with open(output_file, 'wb') as output:
        with requests.Session() as session:
            LOGGER.info(
                'Recording from %s, for %s',
                stream_url,
                datetime.timedelta(seconds=duration),
            )
            
            response = session.get(stream_url, stream=True)
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                elapsed_time = time.time() - start_time

                if chunk:
                    written_bytes += len(chunk)
                    output.write(chunk)
                if elapsed_time >= duration:
                    break

    LOGGER.info('Recorded %d bytes, saved in: %s', written_bytes, output_file)
    return written_bytes

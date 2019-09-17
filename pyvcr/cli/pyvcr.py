"""PyVCR - A tool to record video streams.

Usage:
  pyvcr record --url <url> --output <output> (--start <start> --end <end> | --duration <duration>)
  pyvcr watch <configuration>

Options:
  --stream, -u              Stream URL.
  --output, -o              Output file.
  --start, -s               Record start date time.
  --end, -e                 Record end date time.
  --duration, -d            Record duration (in seconds).
"""
import logging
import datetime
import time

import dateutil.parser
import docopt

from pyvcr import record_stream
from pyvcr import __version__

LOGGER = logging.getLogger(__name__)


def record(stream_url, output_file, start, end, duration):
    """Record `stream_url` in `output_file`.

    :param stream_url: `string` URL of the stream.
    :param output_file: `string` path to the output file.
    :param start: `string` start date time.
    :param end: `string` end date time.
    :param duration: `int` duration in seconds.
    """
    assert (start and end) or duration, (
        'Need to provide either a start/end, or a duration.')

    if start and end:
        # Infer duration from start/end time
        now = datetime.datetime.now()
        start = dateutil.parser.parse(start)
        end = dateutil.parser.parse(end)
        duration = (end - max(now, start)).total_seconds()

        assert end > now, 'The end time can not be in the past.'
        assert duration > 0, 'Duration can not be <= 0 seconds.'

        # Wait for the record to start if needed
        if start > now:
            delta = start - now
            LOGGER.info('The record will start in %s', delta)
            time.sleep(delta.total_seconds())
    else:
        duration = int(duration)

    record_stream(
        stream_url=stream_url,
        output_file=output_file,
        duration=duration,
    )


def watch(configuration_path):
    """Read configuration and start recording when needed.

    :param configuration_path: `string` configuration path.
    """
    pass
    

def main():
    args = docopt.docopt(__doc__, version=__version__)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(module)s:%(lineno)d %(levelname)s - %(message)s',
    )

    if args['record']:
        record(
            stream_url=args['<url>'],
            output_file=args['<output>'],
            start=args['<start>'],
            end=args['<end>'],
            duration=args['<duration>'],
        )
    elif args['watch']:
        watch(
            configuration_path=args['<configuration>'],
        )


if __name__ == '__main__':
    main()

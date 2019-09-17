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
"""  # noqa
import datetime
import logging
import multiprocessing
import os
import time

import dateutil.parser
import dateutil.tz
import docopt

from pyvcr import record_stream, load_configuration
from pyvcr import __version__

LOGGER = logging.getLogger(__name__)


def record(stream_url, output_file, start=None, end=None, duration=None):
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
        assert start.tzinfo == end.tzinfo, (
            'Start and end must be on the same timezone.')

        # Infer duration from start/end time
        now = datetime.datetime.now(tz=start.tzinfo)
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


def _record(args):
    # TODO: Ugly hack to unpack record arguments
    record(**args)


def watch(configuration_path):
    """Read configuration and start recording when needed.

    :param configuration_path: `string` configuration path.
    """
    LOGGER.info('Loading configuration from: %s', configuration_path)

    configuration = load_configuration(configuration_path=configuration_path)
    timezone = dateutil.tz.gettz(configuration['timezone'])
    now = datetime.datetime.now(timezone)
    jobs = []

    for conf_record in configuration['records']:
        LOGGER.info('Checking %s', conf_record['output'])

        start = dateutil.parser.parse(
            conf_record['start']).replace(tzinfo=timezone)
        end = dateutil.parser.parse(
            conf_record['end']).replace(tzinfo=timezone)
        output = os.path.join(
            configuration['output_directory'], conf_record['output'])

        assert end > start, 'Start time must be < end time.'

        if now > start:
            LOGGER.info(
                '%s broadcast already started, skipping',
                conf_record['output'])
            continue

        jobs.append({
            'stream_url': conf_record['stream_url'],
            'output_file': output,
            'start': start,
            'end': end,
        })

    with multiprocessing.Pool(processes=16) as pool:
        pool.map(_record, jobs)


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

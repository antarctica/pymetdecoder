################################################################################
# pymetdecoder/__main__.py
#
# Main executable for pymetdecoder
#
# TDBA 2025-01-08
#   * First version
# TDBA 2025-01-15:
#   * Added METAR
################################################################################
# CONFIGURATION
################################################################################
import sys, argparse, json, logging, warnings
from pymetdecoder import synop, metar, logger

REPORT_TYPES = [
    ("synop", "SYNOP", synop),
    ("metar", "METAR", metar)
]

# Setup logging
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
logger.addHandler(handler)
logging.captureWarnings(True)
warnings_logger = logging.getLogger("py.warnings")
warnings_logger.addHandler(handler)

# Setup command line arguments
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help="Action to take")
subparser_decode = subparsers.add_parser("decode", help="Decode reports")
subparser_encode = subparsers.add_parser("encode", help="Encode reports")
subparser_decode.add_argument("--include-original", "-o", action="store_true",
    help="Include the original message in the output")
for r in REPORT_TYPES:
    subparser_decode.add_argument("--{}".format(r[0]), dest="d_{}".format(r[0]),
        nargs="*", metavar=r[1], help="{} reports to decode. Use '-' to read from standard input".format(r[1]))
    subparser_encode.add_argument("--{}".format(r[0]), dest="e_{}".format(r[0]),
        nargs="*", metavar=r[1], help="{} reports to encode. Use '-' to read from standard input".format(r[1]))
################################################################################
# FUNCTIONS
################################################################################
def warning_fmt(msg, *args, **kwargs):
    return str(msg)
warnings.formatwarning = warning_fmt
################################################################################
# MAIN
################################################################################
if __name__ == "__main__":
    # Read command line arguments
    args = parser.parse_args()

    # Decode/encode everything as required
    result = {}
    for r in REPORT_TYPES:
        report_obj = getattr(r[2], r[1])

        # Decode
        _d_var = "d_{}".format(r[0])
        if hasattr(args, _d_var) and getattr(args, _d_var) is not None:
            if r[0] not in result:
                result[r[0]] = { "decoded": [] }
                if args.include_original:
                    result[r[0]]["messages"] = []

            for msg in getattr(args, _d_var):
                try:
                    if msg == "-": # Read from standard input
                        for line in sys.stdin:
                            result[r[0]]["decoded"].append(report_obj().decode(line))
                            if args.include_original:
                                result[r[0]]["messages"].append(line)
                    else: # Read from command line
                        result[r[0]]["decoded"].append(report_obj().decode(msg))
                        if args.include_original:
                            result[r[0]]["messages"].append(msg)
                except Exception as e:
                    logger.error(str(e))

        # Encode
        _e_var = "e_{}".format(r[0])
        if hasattr(args, _e_var) and getattr(args, _e_var) is not None:
            if r[0] not in result:
                result[r[0]] = {}

            for msg in getattr(args, _e_var):
                try:
                    if msg == "-": # Read from standard input
                        for line in sys.stdin:
                            result[r[0]].append(report_obj().encode(json.loads(line)))
                    else: # Read from command line
                        result[r[0]].append(report_obj().encode(json.loads(msg)))
                except Exception as e:
                    logger.error(str(e))

    # Print the result
    print(json.dumps(result))

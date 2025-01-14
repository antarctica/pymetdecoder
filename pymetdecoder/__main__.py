################################################################################
# pymetdecoder/__main__.py
#
# Main executable for pymetdecoder
#
# TDBA 2025-01-08
#   * First version
################################################################################
# CONFIGURATION
################################################################################
import sys, argparse, json
from pymetdecoder import synop

REPORT_TYPES = [("synop", "SYNOP", synop)]

# Setup command line arguments
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help="Action to take")
subparser_decode = subparsers.add_parser("decode", help="Decode reports")
subparser_encode = subparsers.add_parser("encode", help="Encode reports")
for r in REPORT_TYPES:
    subparser_decode.add_argument("--{}".format(r[0]), action="append", dest="d_{}".format(r[0]),
        help="{} reports to decode. Use '-' to read from standard input".format(r[1]))
    subparser_decode.add_argument("--include-original", "-o", action="store_true",
        help="Include the original message in the output")
    subparser_encode.add_argument("--{}".format(r[0]), action="append", dest="e_{}".format(r[0]),
        help="{} reports to encode. Use '-' to read from standard input".format(r[1]))
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
        if hasattr(args, _d_var):
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
                    print("ERROR: {}".format(str(e)))
    
        # Encode
        _e_var = "e_{}".format(r[0])
        if hasattr(args, _e_var):
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
                    print("ERROR: {}".format(str(e)))

    # Print the result
    print(result)

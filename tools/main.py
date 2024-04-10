import argparse
import subprocess
from optimal_finder import run

PROGRAM_NAME = "OpenSearch Optimal Finder"
DEFAULT_CLIENT_OPTIONS = "timeout:60"

def configure_runner_parser(p):
    p.add_argument(
        "--target-hosts",
        help="Define a comma-separated list of host:port pairs which should be targeted if using the pipeline 'benchmark-only' "
             "(default: localhost:9200).",
        default="")  # actually the default is pipeline specific and it is set later
    p.add_argument(
        "--client-options",
        help=f"Define a comma-separated list of client options to use. The options will be passed to the OpenSearch "
             f"Python client (default: {DEFAULT_CLIENT_OPTIONS}).",
        default=DEFAULT_CLIENT_OPTIONS)

    p.add_argument("--bulk-size", type=int, default=100, help="Define the bulk size of _bulk API.")
    p.add_argument("--bulk-size-schedule", help="Define the bulk size test schedule.")
    p.add_argument("--client", type=int, default=1, help="client number.")
    p.add_argument("--client-schedule", help="number of client test schedule.")
    p.add_argument("--workload-path", help="Define the path to a workload.")
    p.add_argument("--batch-size", type=int, default=1, help="batch number.")
    p.add_argument("--batch-size-schedule", help="Define the bulk size test schedule.")
    p.add_argument("--total-data-size", type=int, default=0,
                   help="Total data size for a single test, we'll only use the first"
                   " {{total-data-size}} document to run each test")
    p.add_argument("--allowed-error-rate", type=float, default=0,
                   help="Allowed maximum error rate for each test, "
                   "exceeding the value would fail a test")
    p.add_argument("--remote-ml-server-type", choices=["sagemaker", "cohere", "openai", "unknown"], 
                   default="unknown", help="Set remote ML server type to use recommended test set up")


def construct_parser():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description="An automation tool for OpenSearch to identify the optimal parameter for ingestion.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand", help="")

    runner_parser = subparsers.add_parser("run", help="run command directly")
    notebook_parser = subparsers.add_parser("notebook", help="launch notebook")
    configure_runner_parser(runner_parser)
    return parser


def main():
    parser = construct_parser()
    args = parser.parse_args()
    subcommand = args.subcommand
    if subcommand == "run":
        run_command(args)
    elif subcommand == "notebook":
        run_notebook()


def run_command(args):
    return run(args)


def run_notebook():
    subprocess.run(["jupyter", "notebook"])


if __name__=="__main__":
    main()

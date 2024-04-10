import os
import sys
import csv
import uuid
import logging
import tempfile
import subprocess
from datetime import datetime
from timeit import default_timer as timer
from schedule import BatchSizeSchedule, BulkSizeSchedule, ClientSchedule

ERROR_RATE_KEY="error rate"


def get_benchmark_params(args, batch_size, bulk_size, number_of_client, temp_output_file):
    params = {}
    params["--target-hosts"] = args.target_hosts
    if args.client_options:
        params["--client-options"] = args.client_options
    params["--kill-running-processes"] = None
    # we only test remote cluster
    params["--pipeline"] = "benchmark-only"
    params["--telemetry"] = "node-stats"
    params["--telemetry-params"] = "node-stats-include-indices:true,node-stats-sample-interval:10,node-stats-include-mem:true,node-stats-include-process:true"
    params["--workload-path"] = args.workload_path
    params["--workload-params"] = get_workload_params(batch_size, bulk_size, number_of_client)
    # generate output
    params["--results-format"] = "csv"
    params["--results-file"] = temp_output_file
    return params


def get_workload_params(batch_size, bulk_size, number_of_client):
    params = [f"bulk_size:{bulk_size}",
              f"batch_size:{batch_size}",
              f"bulk_indexing_clients:{number_of_client}",
              f"index_name:{generate_random_index_name()}"]

    return ",".join(params)


def run_benchmark(params):
    commands = ["opensearch-benchmark", "execute-test"]
    for k, v in params.items():
        commands.append(k)
        if v:
            commands.append(v)

    proc = None
    try:
        proc = subprocess.Popen(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        stdout, stderr = proc.communicate()
        return proc.returncode == 0, stderr.decode('ascii')
    except KeyboardInterrupt as e:
        proc.terminate()
        print("Process is terminated!")
        raise e


def generate_random_index_name():
    return str(datetime.now().timestamp()) + "_" + str(uuid.uuid4())


class Result(object):
    def __init__(self, test_id, batch_size, bulk_size, number_of_client):
        self.success = None
        self.test_id = test_id
        self.batch_size = batch_size
        self.bulk_size = bulk_size
        self.number_of_client = number_of_client
        self.total_time = 0
        self.error_rate = 0
        self.output = None

    def set_output(self, success, total_time, output):
        self.success = success
        self.total_time = total_time
        if not output:
            return
        self.output = output
        self.error_rate = float(output[ERROR_RATE_KEY]) if ERROR_RATE_KEY in output else 0 # percentage
        

def run(args):
    logger = logging.getLogger(__name__)
    batches = BatchSizeSchedule(args).steps
    bulks = BulkSizeSchedule(args).steps
    number_of_clients = ClientSchedule(args).steps
    results = {}
    success_result_ids = []
    success_count = 0
    failure_count = 0

    total = len(batches) * len(bulks) * len(number_of_clients)
    print(f"There will be {total} tests to run with {len(batches)} batch sizes, { len(bulks)} bulk sizes, "
          f"{len(number_of_clients)} client numbers.")
    i = 0
    for client in number_of_clients:
        for bulk in bulks:
            for batch in batches:
                i = i + 1
                print(f'{i}/{total} - Running with number of client: {client}, batch size: {batch}, bulk size: {bulk}. '
                      f'Total: {success_count} success, {failure_count} failures')
                test_id = str(uuid.uuid4())
                results[test_id] = Result(test_id, batch, bulk, client)
                new_file, filename = tempfile.mkstemp()
                params = get_benchmark_params(args, batch, bulk, client, filename)

                success = False
                err = None
                start = timer()
                try:
                    success, err = run_benchmark(params)
                finally:
                    end = timer()
                    if success:
                        success_count = success_count + 1
                        with open(filename, newline='') as csvfile:
                            line_reader = csv.reader(csvfile, delimiter=',')
                            output = {}
                            for row in line_reader:
                                output[row[0]] = row[2]
                            results[test_id].set_output(True, int(end - start), output)
                            if results[test_id].error_rate <= args.allowed_error_rate:
                                success_result_ids.append(test_id)
                    else:
                        logger.error(err)
                        failure_count = failure_count + 1
                        results[test_id].set_output(False, int(end - start), None)

                os.remove(filename)

    optimal = find_optimal_result([results[id] for id in success_result_ids])
    if not optimal:
        print("All tests failed, couldn't find any results!")
    else:
        print(f"the optimal batch size is: {optimal.batch_size}")
    return results


def find_optimal_result(results):
    total_time = sys.maxsize
    optimal = None
    for result in results:
        if result.total_time < total_time:
            total_time = result.total_time
            optimal = result
    return optimal


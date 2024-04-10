# An OpenSearch ingestion variable tuning tool
When ingesting data to OpenSearch using bulk API, using different variables could result in different ingestion performance. For example, the amount of document in bulk API, how many OpenSearch clients are used to send requests etc. It's not easy for user to experiment with all the combinations of the variables and find the option which could lead to optimal ingestion performance. In OpenSearch-2.15.0, a new parameter "batch size" was introduced in bulk API which could significantly reduce
ingestion time when using with `text_embedding` processor and `sparse_encoding` processor. However, this additional impactor could make the variable tuning even more difficult.

This tool is to help dealing with the pain point of tuning these variables which could impact ingestion performance and automatically find the optimal combination of the variables. It utilizes the OpenSearch-Benchmark, uses different varible combination to run benchmark, collects their outputs, analyzes and visualizes the results. It relies on OpenSearch-Benchmark tool to run benchmark with different variables, records the benchmark results, visualizes and recommends the combination which could lead to optimal ingestion result.

There are three variables that you can test against: bulk size, OS client number, batch size. If you already have a perferred value for certain variable, you can simply set it to a fixed value and only test other variables. For example, you always use 1 client to run bulk API with bulk size equals to 100, then you can only try different batch size to see which batch size can have the best performance.

It can be run through command line or through Jupyter Notebook.

## Install
```bash
python3 -m venv tuning
```

```bash
source ./tuning/bin/activate
```

```bash
pip3 install opensearch-benchmark
```

If you want to run the tool through Jupyter Notebook
```bash
pip3 install notebook
```

## Run
Example command:
```bash
python main.py run --target-hosts="{{opensearch host}}" --client-options="{{timeout, username, password etc}}" --workload-path="{{local path of workload}}"
```

### Testing Schedule for variables
All three variables have two different parameters, one to set fixed value and one to set a testing schedule. The schedule has two patterns:
1. set starting value, end value, step size and trend, separated by `:`, e.g. "10:100:1:10" means we should test with "10, 20, 30, 40, 50, 60, 70, 80, 90, 100". "20:100:-1:20" means we should test reversely with "100, 80, 60, 40, 20"。
2. configure testing values manually by adding a prefix symbol `@` and still separate values using `:` e.g. "@10:20:50" means we only test with 10, 20, 50.

### Parameters shared with OpenSearch-Benchmark
We reuse these parameters with OpenSearch-Benchmark `execute-test`:
1. WORKLOAD_PATH same as "--workload-path" in OSB `execute-test`, "Define the path to a workload"
2. TARGET_HOSTS same as "--target-hosts" in OSB `execute-test`, "Define a comma-separated list of host:port pairs which should be targeted if using the pipeline 'benchmark-only' (default: localhost:9200)."
3. CLIENT_OPTIONS same as "--client-options" in OSB `execute-test`, "Define a comma-separated list of client options to use. The options will be passed to the OpenSearch Python client (default: timeout:60)."




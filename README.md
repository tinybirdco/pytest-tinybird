pytest-tinybird
===================================

A pytest plugin to report test results to Tinybird. At the end of every run, this plugin posts results using the [Tinybird Events API](https://www.tinybird.co/docs/ingest/events-api.html). 

[![PyPI version](https://badge.fury.io/py/pytest-tinybird.svg)](https://badge.fury.io/py/pytest-tinybird)
![Passed](https://github.com/jlmadurga/pytest-tinybird/actions/workflows/main.yml/badge.svg)
![Top test passed](https://img.shields.io/endpoint?url=https://api.tinybird.co/v0/pipes/top_test_passed.ndjson?token=p.eyJ1IjogIjNhZjhlMTBhLTM2MjEtNDQ3OC04MWJmLTE5MDQ5N2UwNjBjYiIsICJpZCI6ICJkNDNmZGQ2Ni03NzY1LTQzZGYtYjEyNS0wYzNjYWJiMDgxZjUifQ.yWypEczMfJlgkjNt29pCf45XaxE1dMOr-oznll5tjpY)



Requirements
------------

- Python >=3.8
- pytest 3.8 or newer (previous versions might be compatible)
- [Tinybird account](https://www.tinybird.co/) and a [token with append permissions](https://www.tinybird.co/docs/concepts/auth-tokens.html?highlight=token#auth-token-scopes)


Installation
------------

pypi install package: https://pypi.org/project/pytest-tinybird/

You can install the plugin with the following bash command:

```bash
  $ pip install pytest-tinybird
```


Usage
------------

You just need your [Tinybird](https://www.tinybird.co/) account and a Token with append permissions

Set these env variables:

```bash
export TINYBIRD_URL=<https://api.tinybird.co|https://api.us-east.tinybird.co>   # depends on your region
export TINYBIRD_DATASOURCE=<datasource_name>  # will be created with first results posted
export TINYBIRD_TOKEN=<token_with_append_permissions>
```

Then run pytest with `--report-to-tinybird`.


```bash
$ pytest tests --report-to-tinybird
```

CI execution info can also be set using some env variables. These are from GitLab:

```bash
CI_COMMIT_SHA
CI_COMMIT_BRANCH
CI_JOB_ID
CI_JOB_NAME
CI_JOB_URL
```

If you are not using GitLab, you will need to set them manually. For instance, for GitHub actions you can check our current [GitHub actions workflow](https://github.com/tinybirdco/pytest-tinybird/blob/master/.github/workflows/main.yml).

Data Source details
--------------------

The `pytest-tinybird` plugin creates and sends `report` objects via the [Events API](https://www.tinybird.co/docs/ingest/events-api.html) with this structure:

```
{
	'date': now,
	'commit': self.commit,
	'branch': self.branch,
	'job_id': self.job_id,
	'job_url': self.job_url,
	'job_name': self.job_name,
	'test_nodeid': test.nodeid,
	'test_name': test.head_line,
	'test_part': test.when,
	'duration': test.duration,
	'outcome': test.outcome
}
```

When a `report` object is first sent to Tinybird, a Data Source with the following definition and schema is created:

```sql
TOKEN "pytest-executor-write" APPEND

SCHEMA >
    `commit` String `json:$.commit`,
    `branch` String `json:$.branch`,
    `date` DateTime `json:$.date`,
    `duration` Float32 `json:$.duration`,
    `job_id` String `json:$.job_id`,
    `job_name` String `json:$.job_name`,
    `job_url` String `json:$.job_url`,
    `outcome` LowCardinality(String) `json:$.outcome`,
    `test_name` String `json:$.test_name`,
    `test_nodeid` String `json:$.test_nodeid`,
    `test_part` LowCardinality(String) `json:$.test_part`

ENGINE MergeTree
ENGINE_PARTITION_KEY toYYYYMM(date)
```

You can also see the Data Source schema with this [data sample](https://api.tinybird.co/v0/pipes/ci_tests_sample.json?token=p.eyJ1IjogIjNhZjhlMTBhLTM2MjEtNDQ3OC04MWJmLTE5MDQ5N2UwNjBjYiIsICJpZCI6ICIwNzMwZTJjYy1mYzA4LTQxMDMtOTMwNy1jMThjYWY5OGI4OGUifQ.kpCQfin0KFC8olEju1qVqDH14nlSzGgqjAWpl1k7RUI)
from an API Endpoint created from the Data Source the `pytest-tinybird` plugin populates.

pytest-tinybird
===================================

A pytest plugin to report test results to tinybird

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

```bash
  $ pip install pytest-tinybird
```



Usage
------------

You just need a [tinybird](https://www.tinybird.co/) account and token with append permissions

Set these env variables:

```bash
export TINYBIRD_URL=<https://api.tinybird.co|https://api.us-east.tinybird.co>   # depends on your region
export TINYBIRD_DATASOURCE=<datasource_name>  # will be created with first results posted
export TINYBIRD_TOKEN=<token_with_append_permissions>
```

Just run pytest with `--report-to-tinybird`.


```bash
$ pytest tests --report-to-tinybird
```

CI execution info is filled using some env variables, the ones from GitLab.


```bash
CI_COMMIT_SHA
CI_COMMIT_BRANCH
CI_JOB_ID
CI_JOB_NAME
CI_JOB_URL
```

In case you are not using GitLab you need to set it manually. For instance for GitHub actions you can check our current [GitHub actions workflow](https://github.com/tinybirdco/pytest-tinybird/blob/master/.github/workflows/main.yml))


You can check the data source schema with this [data sample](https://api.tinybird.co/v0/pipes/ci_tests_sample.json?token=p.eyJ1IjogIjNhZjhlMTBhLTM2MjEtNDQ3OC04MWJmLTE5MDQ5N2UwNjBjYiIsICJpZCI6ICIwNzMwZTJjYy1mYzA4LTQxMDMtOTMwNy1jMThjYWY5OGI4OGUifQ.kpCQfin0KFC8olEju1qVqDH14nlSzGgqjAWpl1k7RUI)
of this repo CI executions.

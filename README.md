pytest-tinybird
===================================

A pytest plugin to report test results to tinybird

![Passed](https://github.com/jlmadurga/pytest-tinybird/actions/workflows/main.yml/badge.svg)
![Top test passed](https://img.shields.io/endpoint?url=https://api.tinybird.co/v0/pipes/top_test_passed.ndjson?token=p.eyJ1IjogIjNhZjhlMTBhLTM2MjEtNDQ3OC04MWJmLTE5MDQ5N2UwNjBjYiIsICJpZCI6ICJkNDNmZGQ2Ni03NzY1LTQzZGYtYjEyNS0wYzNjYWJiMDgxZjUifQ.yWypEczMfJlgkjNt29pCf45XaxE1dMOr-oznll5tjpY)


Requirements
------------

- Python >=3.8
- pytest 3.8 or newer (previous versions might be compatible)


Installation
------------

```bash
  $ python setup.py install
```

Not via `pip` yet


Usage
------------

You just need a [tinybird](https://www.tinybird.co/) account and token with append permissions

Set this env variables

```bash
  TINYBIRD_URL=<https://api.tinybird.co|https://api.us-east.tinybird.co>   # depends on your region
  TINYBIRD_DATASOURCE=<datasource_name>  # will be created with first results posted
  TINYBIRD_TOKEN=<token_with_append_permissions>
```

Just run pytest with `--report-to-tinybird`. 


```bash
$ pytest tests --report-to-tinybird
```

CI execution info is filled using some env variables, the ones from GitLab.


```bash
CI_COMMIT_SHA
CI_JOB_ID
CI_JOB_NAME
CI_JOB_URL
```

In case you are not using GitLab you need to set it manually. For instance for GitHub actions you can check 
current [GitHub actions workflow](.github/workflows/main.yml))

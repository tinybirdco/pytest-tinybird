import os
import logging
from typing import Union
from datetime import datetime
import json

import requests
import pytest
from _pytest.config import ExitCode, Config
from _pytest.main import Session
from _pytest.terminal import TerminalReporter

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 2


class TinybirdReport:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = os.environ.get("TINYBIRD_URL")
        self.datasource_name = os.environ.get("TINYBIRD_DATASOURCE")
        self.token = os.environ.get("TINYBIRD_TOKEN")
        self.url = f"{self.base_url}/v0/events?name={self.datasource_name}&token={self.token}"
        self.commit = os.environ.get('CI_COMMIT_SHA', 'ci_commit_sha_unknown')
        self.job_id = os.environ.get('CI_JOB_ID', 'ci_job_id_unknown')
        self.job_url = os.environ.get('CI_JOB_URL', 'job_url_unknown')
        self.job_name = os.environ.get('CI_JOB_NAME', 'job_name_unknown')
        self.branch = os.environ.get(
            'CI_MERGE_REQUEST_SOURCE_BRANCH_NAME',
            os.environ.get('CI_COMMIT_BRANCH', 'ci_commit_branch_unknown')
        )

    def report(self, session: Session):
        if None in [self.base_url, self.datasource_name, self.token]:
            log.error("Required values for environment variables")
            return
        now = str(datetime.now())
        terminalreporter: TerminalReporter = session.config.pluginmanager.get_plugin(
            "terminalreporter"
        )
        # special check for pytest-xdist plugin, we do not want to send report for each worker.
        if hasattr(terminalreporter.config, 'workerinput'):
            return
        report = []
        for k in terminalreporter.stats:
            for test in terminalreporter.stats[k]:
                try:
                    report.append({
                        'date': now,
                        'commit': self.commit,
                        'job_id': self.job_id,
                        'job_url': self.job_url,
                        'job_name': self.job_name,
                        'test_nodeid': test.nodeid,
                        'test_name': test.head_line,
                        'test_part': test.when,
                        'duration': test.duration,
                        'outcome': test.outcome,
                        'branch': self.branch
                    })
                except AttributeError:
                    pass
        data = '\n'.join(json.dumps(x) for x in report)
        # This goes to the Internal workspace in EU
        response = requests.post(
            self.url,
            data=data,
            timeout=REQUEST_TIMEOUT)
        if response.status_code != 202:
            log.error("Error while uploading to tinybird %s", response.status_code)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Session, exitstatus: Union[int, ExitCode]):
        try:
            self.report(session)
        except Exception as e:
            log.error("Tinybird report error: %s - %s", self.url, e)
            raise e

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(
            self,
            terminalreporter: TerminalReporter,
            exitstatus: Union[int, ExitCode],
            config: Config,
    ):
        terminalreporter.write_sep("-", "send report to Tinybird")

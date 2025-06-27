import json
import logging
import os
import time
from datetime import datetime
from typing import Union

import pytest
import requests
from _pytest.config import Config, ExitCode
from _pytest.main import Session
from _pytest.terminal import TerminalReporter

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 2
MAX_PAYLOAD_SIZE_MB = 10
MAX_PAYLOAD_SIZE_BYTES = MAX_PAYLOAD_SIZE_MB * 1024 * 1024  # 10MB in bytes


class TinybirdReport:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = os.environ.get("TINYBIRD_URL")
        self.timeout = int(os.environ.get("TINYBIRD_TIMEOUT", REQUEST_TIMEOUT))
        self.retries = int(os.environ.get('TINYBIRD_RETRIES', 0))
        self.wait = os.environ.get("TINYBIRD_WAIT", "false")
        self.datasource_name = os.environ.get("TINYBIRD_DATASOURCE")
        self.token = os.environ.get("TINYBIRD_TOKEN")
        self.commit = os.environ.get('CI_COMMIT_SHA', 'ci_commit_sha_unknown')
        self.job_id = os.environ.get('CI_JOB_ID', 'ci_job_id_unknown')
        self.job_url = os.environ.get('CI_JOB_URL', 'job_url_unknown')
        self.job_name = os.environ.get('CI_JOB_NAME', 'job_name_unknown')
        self.branch = os.environ.get(
            'CI_MERGE_REQUEST_SOURCE_BRANCH_NAME',
            os.environ.get('CI_COMMIT_BRANCH', 'ci_commit_branch_unknown')
        )
        self.url = f"{self.base_url}/v0/events?name={self.datasource_name}" \
                   f"&token={self.token}" \
                   f"&wait={self.wait}"

        # optional values for multi-repository and multi-workflow usage
        self.repository = os.environ.get('CI_REPOSITORY_NAME', None)
        self.workflow = os.environ.get('CI_WORKFLOW_NAME', None)

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
                    report_entry = {
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
                    report_optionals = {
                        'repository': self.repository,
                        'workflow': self.workflow
                    }
                    # only add optional values if they're not None
                    report_entry.update({k: v for k, v
                                         in report_optionals.items()
                                         if v is not None})
                    report.append(report_entry)
                except AttributeError:
                    pass
        
        # Convert report to data string and check if chunking is needed
        full_data = '\n'.join(json.dumps(x) for x in report)
        full_data_size_bytes = len(full_data.encode('utf-8'))
        
        if full_data_size_bytes <= MAX_PAYLOAD_SIZE_BYTES:
            # Single request is sufficient
            self._send_data(full_data)
        else:
            # Need to chunk the data into multiple requests
            log.info(
                "Payload size (%d bytes, %.2f MB) exceeds maximum limit of %d MB. "
                "Chunking into multiple requests.",
                full_data_size_bytes, 
                full_data_size_bytes / (1024 * 1024),
                MAX_PAYLOAD_SIZE_MB
            )
            
            chunks = self._chunk_report_data(report)
            log.info("Sending %d chunks to stay within %d MB limit per request", len(chunks), MAX_PAYLOAD_SIZE_MB)
            
            for i, chunk_data in enumerate(chunks, 1):
                log.debug("Sending chunk %d/%d (%.2f MB)", i, len(chunks), len(chunk_data.encode('utf-8')) / (1024 * 1024))
                self._send_data(chunk_data)

    def _chunk_report_data(self, report):
        """Split report data into chunks that fit within the size limit."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for entry in report:
            entry_data = json.dumps(entry)
            entry_size = len((entry_data + '\n').encode('utf-8'))
            
            # If a single entry exceeds the limit, we still need to include it
            # (this is an edge case that should rarely happen)
            if entry_size > MAX_PAYLOAD_SIZE_BYTES:
                log.warning("Single test entry exceeds %d MB limit (%.2f MB). Including in separate chunk.", 
                           MAX_PAYLOAD_SIZE_MB, entry_size / (1024 * 1024))
                if current_chunk:
                    chunks.append('\n'.join(json.dumps(x) for x in current_chunk))
                    current_chunk = []
                    current_size = 0
                chunks.append(entry_data)
                continue
            
            # Check if adding this entry would exceed the limit
            if current_size + entry_size > MAX_PAYLOAD_SIZE_BYTES and current_chunk:
                # Finalize current chunk and start a new one
                chunks.append('\n'.join(json.dumps(x) for x in current_chunk))
                current_chunk = [entry]
                current_size = entry_size
            else:
                # Add entry to current chunk
                current_chunk.append(entry)
                current_size += entry_size
        
        # Add the last chunk if it has any entries
        if current_chunk:
            chunks.append('\n'.join(json.dumps(x) for x in current_chunk))
        
        return chunks

    def _send_data(self, data):
        """Send data to Tinybird with retry logic."""
        for attempt in range(self.retries + 1):
            try:
                # This goes to the Internal workspace in EU
                response = requests.post(
                    self.url,
                    data=data,
                    timeout=self.timeout
                )
                if response.status_code in [200, 202]:
                    return  # Success, exit retry loop
                log.error("Error while uploading to tinybird %s (Attempt %s/%s)",
                          response.status_code, attempt + 1, self.retries + 1)
            except requests.exceptions.RequestException as e:
                log.error("Request failed: %s (Attempt %s/%s)",
                          e, attempt + 1, self.retries + 1)
            if attempt < self.retries:
                time.sleep(2 ** attempt)
        else:
            log.error("All %s attempts failed to upload to tinybird", self.retries + 1)

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

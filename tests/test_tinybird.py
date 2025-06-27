import random
from unittest import mock
import os


def test_report_to_tinybird(testdir):

    # create a temporary pytest test module
    testdir.makepyfile("""
        import pytest
        from random import randint
        def test_passed():
            assert True
        def test_flaky():
            assert randint(1,10) >=5
        """)

    tinybird_url = os.environ["TINYBIRD_URL"] = 'https://fake-api.tinybird.co'
    datasource_name = os.environ["TINYBIRD_DATASOURCE"] = "test_datasource"
    tinybird_token = os.environ["TINYBIRD_TOKEN"] = 'test_token'
    timeout = os.environ["TINYBIRD_TIMEOUT"] = "10"
    wait = os.environ["TINYBIRD_WAIT"] = random.choice(['true', 'false'])

    with mock.patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200 if wait == 'true' else 202
        testdir.runpytest(
            "-n 2",
            '--report-to-tinybird',
            '-vvv'
        )
        mock_post.assert_called_once_with(f"{tinybird_url}/v0/events?name={datasource_name}"
                                          f"&token={tinybird_token}"
                                          f"&wait={wait}",
                                          data=mock.ANY,
                                          timeout=int(timeout))


def test_retry_to_tinybird(testdir):
    # create a temporary pytest test module
    testdir.makepyfile("""
        import pytest
        def test_passed():
            assert True
        """)

    os.environ["TINYBIRD_URL"] = 'https://fake-api.tinybird.co'
    os.environ["TINYBIRD_DATASOURCE"] = "test_datasource"
    os.environ["TINYBIRD_TOKEN"] = 'test_token'
    os.environ["TINYBIRD_TIMEOUT"] = "1"
    os.environ["TINYBIRD_RETRIES"] = "1"

    with mock.patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 503
        testdir.runpytest(
            "-n 1",
            '--report-to-tinybird',
            '-vvv'
        )
        assert mock_post.call_count == 2


def test_payload_size_limit_truncation(testdir):
    """Test that payloads exceeding 10MB are truncated to stay within limit"""
    
    # Create a test file that will generate many test cases
    test_content = """
import pytest

"""
    
    # Generate many test functions to create a large payload that definitely exceeds 10MB
    for i in range(15000):  # This will create a payload > 10MB
        test_content += f"""
def test_large_payload_{i}():
    '''This is a test with a very long description that will contribute to payload size: {"x" * 500}'''
    assert True
"""
    
    testdir.makefile('.py', test_large_payload=test_content)

    os.environ["TINYBIRD_URL"] = 'https://fake-api.tinybird.co'
    os.environ["TINYBIRD_DATASOURCE"] = "test_datasource"
    os.environ["TINYBIRD_TOKEN"] = 'test_token'
    os.environ["TINYBIRD_TIMEOUT"] = "10"
    os.environ["TINYBIRD_WAIT"] = "false"

    with mock.patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 202
        
        # Capture the data parameter to verify truncation
        captured_data = ""
        
        def capture_data(*args, **kwargs):
            nonlocal captured_data
            captured_data = kwargs.get('data', '')
            data_size_bytes = len(captured_data.encode('utf-8'))
            max_size_bytes = 10 * 1024 * 1024  # 10MB
            assert data_size_bytes <= max_size_bytes, f"Payload size {data_size_bytes} exceeds {max_size_bytes} bytes"
            return mock.Mock(status_code=202)
        
        mock_post.side_effect = capture_data
        
        testdir.runpytest(
            '--report-to-tinybird',
            '-v'
        )
        
        # Verify exactly one request was made (truncation, not chunking)
        assert mock_post.call_count == 1, f"Expected single request with truncation, but got {mock_post.call_count}"
        
        # Verify captured_data was set
        assert captured_data is not None and captured_data != "", "No data was captured from the request"
        
        # Verify the payload is within the size limit
        data_size_bytes = len(captured_data.encode('utf-8'))
        max_size_bytes = 10 * 1024 * 1024  # 10MB
        assert data_size_bytes <= max_size_bytes, f"Truncated payload size {data_size_bytes} exceeds {max_size_bytes} bytes"
        
        # Verify some data is present (not completely empty)
        assert len(captured_data) > 0, "Payload should contain some test data"
        
        # Verify early tests are preserved (truncation keeps first entries)
        assert 'test_large_payload_0' in captured_data, "First test should be preserved in truncated data"
        
        # Verify later tests are truncated (last tests should be missing)
        assert 'test_large_payload_14999' not in captured_data, "Last test should be truncated"
        
        print(f"Successfully truncated large payload to stay within 10MB limit")

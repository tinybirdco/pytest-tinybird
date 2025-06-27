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


def test_payload_size_limit_chunking(testdir):
    """Test that payloads exceeding 10MB are chunked into multiple requests"""
    
    # Create a test file that will generate many test cases
    test_content = """
import pytest

"""
    
    # Generate many test functions to create a large payload that definitely exceeds 10MB
    for i in range(15000):  # Increased to ensure payload > 10MB
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
        
        # Capture all data parameters to verify chunking
        all_request_data = []
        
        def capture_data(*args, **kwargs):
            data = kwargs.get('data', '')
            all_request_data.append(data)
            data_size_bytes = len(data.encode('utf-8'))
            max_size_bytes = 10 * 1024 * 1024  # 10MB
            assert data_size_bytes <= max_size_bytes, f"Chunk size {data_size_bytes} exceeds {max_size_bytes} bytes"
            return mock.Mock(status_code=202)
        
        mock_post.side_effect = capture_data
        
        testdir.runpytest(
            '--report-to-tinybird',
            '-v'
        )
        
        # Verify multiple requests were made (chunking occurred)
        assert mock_post.call_count > 1, f"Expected multiple requests for chunking, but got {mock_post.call_count}"
        
        # Verify each chunk is within the size limit
        for i, data in enumerate(all_request_data):
            chunk_size = len(data.encode('utf-8'))
            max_size_bytes = 10 * 1024 * 1024  # 10MB
            assert chunk_size <= max_size_bytes, f"Chunk {i+1} size {chunk_size} exceeds {max_size_bytes} bytes"
        
        # Verify all data is preserved by checking total content
        combined_data = '\n'.join(all_request_data)
        # Each test should appear in the combined data
        assert 'test_large_payload_0' in combined_data, "First test missing in chunked data"
        assert 'test_large_payload_14999' in combined_data, "Last test missing in chunked data"
        
        print(f"Successfully chunked data into {mock_post.call_count} requests")

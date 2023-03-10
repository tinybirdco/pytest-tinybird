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

    with mock.patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 202
        testdir.runpytest(
            "-n 2",
            '--report-to-tinybird',
            '-vvv'
        )
        mock_post.assert_called_once_with(f"{tinybird_url}/v0/events?name={datasource_name}"
                                          f"&token={tinybird_token}",
                                          data=mock.ANY,
                                          timeout=2)

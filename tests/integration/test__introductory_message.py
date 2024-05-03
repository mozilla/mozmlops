
def test_introductory_message_for_integration(capsys):
    with capsys.disabled():
        print("""
        Your test run currently includes the integration tests for this package.
        These tests require google authentication to test our Google Cloud Storage integration. 
        They also take several seconds to run.

        If you'd like to iterate more quickly in development, 
        you can ignore integration tests with the command:

        pytest --ignore=tests/integration

        Please run the integration tests before publish or release, of course \N{Smiling Face with Open Mouth and Cold Sweat}
        """)

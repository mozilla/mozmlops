
def test_introductory_message_for_integration(capsys):
    """
    Prints an intro message before running the integration tests
    Signalling that they take time and offering a command to skip them.
    """
    with capsys.disabled():
        print("""
        Your test run includes the integration tests for this package.
        These tests require google authentication and also take several seconds to run.

        To iterate more quickly in development, ignore integration tests with the command:

        pytest --ignore=tests/integration

        Please run the integration tests before publish or release, of course \N{Smiling Face with Open Mouth and Cold Sweat}
        """)

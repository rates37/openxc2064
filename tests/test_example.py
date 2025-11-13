from openxc2064 import say_hello


def test_say_hello():
    assert say_hello() == "Hello world!"
    assert say_hello("bro") == "Hello bro!"

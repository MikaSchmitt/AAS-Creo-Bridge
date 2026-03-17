from __future__ import annotations

from aas_adapter import Version


def test_version_class_constructors():
    ver = Version("1.2.3")
    assert ver.major == 1
    assert ver.minor == 2
    assert ver.patch == 3

    ver = Version("AP-4.12")
    assert ver.name == "AP"
    assert ver.major == 4
    assert ver.minor == 12
    assert ver.patch == 0

    ver = Version("5.2.7-alpha")
    assert ver.name == "alpha"
    assert ver.major == 5
    assert ver.minor == 2
    assert ver.patch == 7

    ver = Version("10")
    assert ver.major == 10
    assert ver.minor == 0
    assert ver.patch == 0

    ver = Version("Creo Parametric 10")
    assert ver.name == "Creo Parametric"
    assert ver.major == 10

    try:
        ver = Version("15alpha2")
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"

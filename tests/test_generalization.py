from datetime import date
from data import Gender

from scripts.generalization import (
    generalize_address,
    generalize_birth_date,
    generalize_cap,
    generalize_city,
    generalize_gender,
    generalize_phone_number,
)


def test_generalize_cap():
    assert generalize_cap(16154, 0) == 16154
    assert generalize_cap(16154, 1) == 16150
    assert generalize_cap(16154, 2) == 16100
    assert generalize_cap(16154, 3) == 16000
    assert generalize_cap(16154, 4) == 10000
    assert generalize_cap(16154, 5) == 00000


def test_generalize_birth_date():
    assert generalize_birth_date(date(2222, 2, 2), 0) == date(2222, 2, 2)
    assert generalize_birth_date(date(2222, 2, 2), 1) == date(2222, 2, 1)
    assert generalize_birth_date(date(2222, 2, 2), 2) == date(2222, 1, 1)
    assert generalize_birth_date(date(2222, 2, 2), 3) == date(1, 1, 1)


def test_generalize_gender():
    assert generalize_gender(Gender.MALE, 0) == Gender.MALE
    assert generalize_gender(Gender.FEMALE, 0) == Gender.FEMALE
    assert generalize_gender(Gender.NON_BINARY, 0) == Gender.NON_BINARY
    assert generalize_gender(Gender.MALE, 1) == "*"
    assert generalize_gender(Gender.FEMALE, 1) == "*"
    assert generalize_gender(Gender.NON_BINARY, 1) == "*"


def test_generalize_address():
    assert generalize_address("a,b", 0) == "a,b"
    assert generalize_address("a,b", 1) == "a"
    assert generalize_address("a,b", 2) == ""


def test_generalize_city():
    assert generalize_city("Genova", 0) == "Genova"
    assert generalize_city("Genova", 1) == "GE"
    assert generalize_city("Genova", 2) == "*"


def test_generalize_phone_number():
    assert generalize_phone_number("3791211697", 0) == "3791211697"
    assert generalize_phone_number("3791211697", 1) == "379121169*"
    assert generalize_phone_number("3791211697", 2) == "37912116**"
    assert generalize_phone_number("3791211697", 3) == "3791211***"
    assert generalize_phone_number("3791211697", 4) == "379121****"
    assert generalize_phone_number("3791211697", 5) == "37912*****"
    assert generalize_phone_number("3791211697", 6) == "3791******"
    assert generalize_phone_number("3791211697", 7) == "379*******"
    assert generalize_phone_number("3791211697", 8) == "37********"
    assert generalize_phone_number("3791211697", 9) == "3*********"
    assert generalize_phone_number("3791211697", 10) == "**********"

import os
import pytest
from app.crypto import derive_key, encrypt, decrypt, new_salt, password_strength


def test_new_salt_length():
    assert len(new_salt()) == 16


def test_salts_are_random():
    assert new_salt() != new_salt()


def test_derive_key_length():
    key = derive_key("password", new_salt())
    assert len(key) == 32


def test_same_password_same_salt_gives_same_key():
    salt = new_salt()
    k1 = derive_key("my-password", salt)
    k2 = derive_key("my-password", salt)
    assert k1 == k2


def test_different_salts_give_different_keys():
    k1 = derive_key("same", new_salt())
    k2 = derive_key("same", new_salt())
    assert k1 != k2


def test_encrypt_decrypt_roundtrip():
    key = derive_key("secret", new_salt())
    plaintext = "my super secret password"
    ct = encrypt(key, plaintext)
    assert decrypt(key, ct) == plaintext


def test_encrypt_produces_different_blobs():
    key = derive_key("secret", new_salt())
    ct1 = encrypt(key, "same")
    ct2 = encrypt(key, "same")
    assert ct1 != ct2


def test_encrypt_none_returns_none():
    key = derive_key("secret", new_salt())
    assert encrypt(key, None) is None


def test_decrypt_none_returns_none():
    key = derive_key("secret", new_salt())
    assert decrypt(key, None) is None


def test_wrong_key_raises():
    key1 = derive_key("key1", new_salt())
    key2 = derive_key("key2", new_salt())
    ct = encrypt(key1, "secret")
    with pytest.raises(Exception):
        decrypt(key2, ct)


def test_encrypt_unicode():
    key = derive_key("secret", new_salt())
    plaintext = "p@$$w0rd 日本語 ñoño"
    assert decrypt(key, encrypt(key, plaintext)) == plaintext


def test_ciphertext_min_length():
    key = derive_key("secret", new_salt())
    ct = encrypt(key, "x")
    assert len(ct) >= 29


def test_tampered_ciphertext_raises():
    key = derive_key("secret", new_salt())
    ct = bytearray(encrypt(key, "hello"))
    ct[-1] ^= 0xFF
    with pytest.raises(Exception):
        decrypt(key, bytes(ct))


def test_key_derivation_is_deterministic_across_calls():
    salt = new_salt()
    keys = [derive_key("mypassword!", salt) for _ in range(3)]
    assert all(k == keys[0] for k in keys)


def test_encrypt_empty_string():
    key = derive_key("secret", new_salt())
    assert decrypt(key, encrypt(key, "")) == ""


def test_password_strength_weak():
    assert password_strength("short") == 0


def test_password_strength_fair():
    score = password_strength("longpassword12")
    assert score >= 2


def test_password_strength_strong():
    score = password_strength("Str0ng!Pass#99xx")
    assert score == 5


def test_password_strength_no_special_char():
    score = password_strength("LongPassword123")
    assert score < 5

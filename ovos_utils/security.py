import os
import platform
import random
import string

import pexpect

from ovos_utils.log import LOG

try:
    # pycryptodomex
    from Cryptodome.Cipher import AES
except ImportError:
    # pycrypto + pycryptodome
    try:
        from Crypto.Cipher import AES
    except:
        AES = None


def random_key(key_lenght=16):
    """Generate a random string of letters and digits """
    valid_chars = string.ascii_letters + string.digits
    return ''.join(random.choice(valid_chars) for i in range(key_lenght))


def encrypt(key, text, nonce=None):
    if AES is None:
        LOG.error("run pip install pycryptodomex")
        raise ImportError
    if not isinstance(text, bytes):
        text = bytes(text, encoding="utf-8")
    if not isinstance(key, bytes):
        key = bytes(key, encoding="utf-8")
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(text)
    return ciphertext, tag, cipher.nonce


def decrypt(key, ciphertext, tag, nonce):
    if AES is None:
        LOG.error("run pip install pycryptodomex")
        raise ImportError
    if not isinstance(key, bytes):
        key = bytes(key, encoding="utf-8")
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    try:
        data = cipher.decrypt_and_verify(ciphertext, tag)
        text = data.decode(encoding="utf-8")
        return text
    except Exception as e:
        LOG.error("decryption failed, invalid key?")
        raise


def sudo_exec(cmdline, passwd="root"):
    osname = platform.system()
    if osname == 'Linux':
        prompt = r'\[sudo\] password for %s: ' % os.environ['USER']
    elif osname == 'Darwin':
        prompt = 'Password:'
    else:
        raise SystemError("Unsupported platform")

    child = pexpect.spawn(cmdline)
    idx = child.expect([prompt, pexpect.EOF], 3)
    if idx == 0:  # if prompted for the sudo password
        LOG.debug('sudo password was asked.')
        child.sendline(passwd)
        child.expect(pexpect.EOF)
    return child.before

import string
import secrets

random = secrets.SystemRandom()


def get_random_string(length=12, chars=string.ascii_letters + string.digits)：
    return ''.join(random.choice(chars) for i in range(length))


def get_random_secret():
    chars = string.ascii_lowercase + string.digits + '!@#$%^&*(-_=+)'
    return get_random_string(50, chars)

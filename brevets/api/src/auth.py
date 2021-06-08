from passlib.apps import custom_app_context as pwd_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature

def hash_password(password):
    return pwd_context.encrypt(password)

def verify_password(password, hash_pass):
    return pwd_context.verify(password, hash_pass)

# Token Handling

## Generate an authentication token
def build_auth_token(data, duration, secret_key):
    serializer = Serializer(secret_key, expires_in=duration)
    return serializer.dumps(data).decode('utf-8', 'replace')

## Verify an authentication token
def verify_auth_token(token, secret_key):
    if token is None:
        return False, 'NULL_TOKEN'
    if isinstance(token, str):
        token = token.encode('utf-8', 'replace')

    serializer = Serializer(secret_key)
    try:
        data = serializer.loads(token)
    except SignatureExpired:
        return False, 'EXPIRED_TOKEN'
    except BadSignature:
        return False, 'BAD_TOKEN'
    return True, data


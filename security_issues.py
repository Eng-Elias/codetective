import os, subprocess, pickle, yaml, requests, sqlite3, hashlib, jwt

# ❌ Hardcoded secrets (Trivy "secret" should flag these)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxYZ"

PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
-----END PRIVATE KEY-----"""

def insecure_requests():
    # ❌ SSL verification disabled
    requests.get("https://example.com", verify=False)

def cmd_injection(user_input):
    # ❌ shell=True with unsanitized input
    subprocess.run(f"ls {user_input}", shell=True)

def insecure_deserialization(data_bytes):
    # ❌ Arbitrary code execution risk
    return pickle.loads(data_bytes)

def insecure_yaml(data_str):
    # ❌ Unsafe loader
    return yaml.load(data_str, Loader=None)

def sql_injection(tainted):
    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute("CREATE TABLE users(id INTEGER, name TEXT)")
    # ❌ String concatenation into SQL
    q = "SELECT * FROM users WHERE name = '" + tainted + "'"
    return cur.execute(q).fetchall()

def weak_crypto(pw):
    # ❌ MD5 is weak
    return hashlib.md5(pw.encode()).hexdigest()

def jwt_no_verify(token):
    # ❌ Signature verification disabled
    return jwt.decode(token, options={"verify_signature": False})

if __name__ == "__main__":
    insecure_requests()
    # The following calls are just here for static presence; no real execution:
    # cmd_injection("$(rm -rf /)")
    # insecure_deserialization(b"cos\nsystem\n(S'calc'\ntR.")
    # insecure_yaml("!!python/object/apply:os.system ['calc']")
    # sql_injection("anything' OR '1'='1")
    # weak_crypto("password123")
    # jwt_no_verify("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

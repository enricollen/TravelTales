from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.hashes import SHA256
from datetime import datetime, timedelta

def generate_certificate():
    # Generate a private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Generate a certificate
    subject = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, u'example.com'),
    ])

    issuer = subject  # Self-signed certificate, so issuer is the same as subject

    certificate = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u'example.com')]),
        critical=False,
    ).sign(private_key, SHA256(), default_backend())

    # Convert private key and certificate to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    certificate_pem = certificate.public_bytes(
        encoding=serialization.Encoding.PEM
    )

    return private_key_pem, certificate_pem

# Example usage
private_key, certificate = generate_certificate()

# Save private key and certificate to files
with open('private_key.pem', 'wb') as f:
    f.write(private_key)

with open('certificate.pem', 'wb') as f:
    f.write(certificate)

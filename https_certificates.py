import ipaddress
import os
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple, Sequence

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


class LocalCertificateFiles(NamedTuple):
    ca_certificate: Path
    server_certificate: Path
    server_key: Path
    ca_fingerprint: str


def discover_local_addresses() -> tuple[list[str], list[str]]:
    dns_names = {"localhost", socket.gethostname()}
    ip_addresses = {"127.0.0.1"}
    for family, _, _, _, address in socket.getaddrinfo(
        socket.gethostname(), None, socket.AF_INET
    ):
        if family != socket.AF_INET:
            continue
        ip = ipaddress.ip_address(address[0])
        if ip.is_loopback or ip.is_link_local or ip.is_private:
            ip_addresses.add(str(ip))
    return sorted(dns_names), sorted(ip_addresses)


def ensure_local_tls_certificates(
    certificate_directory: Path,
    dns_names: Sequence[str],
    ip_addresses: Sequence[str],
) -> LocalCertificateFiles:
    certificate_directory.mkdir(parents=True, exist_ok=True)
    ca_key_path = certificate_directory / "local-ca-key.pem"
    ca_certificate_path = certificate_directory / "local-ca.crt"
    server_key_path = certificate_directory / "server-key.pem"
    server_certificate_path = certificate_directory / "server.crt"

    if ca_key_path.exists() != ca_certificate_path.exists():
        raise RuntimeError(
            f"Yerel sertifika dosyaları eksik: {certificate_directory}. "
            "Eksik CA anahtarını veya sertifikasını geri yükleyin ya da bu klasörü kaldırıp yeniden başlatın."
        )

    if ca_key_path.exists():
        ca_key = serialization.load_pem_private_key(
            ca_key_path.read_bytes(),
            password=None,
        )
        ca_certificate = x509.load_pem_x509_certificate(ca_certificate_path.read_bytes())
        if not isinstance(ca_key, rsa.RSAPrivateKey):
            raise RuntimeError("Yerel CA anahtarı desteklenen RSA biçiminde değil.")
        if _public_key_bytes(ca_key.public_key()) != _public_key_bytes(
            ca_certificate.public_key()
        ):
            raise RuntimeError("Yerel CA anahtarı ve sertifikası birbiriyle eşleşmiyor.")
    else:
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, "Filament Etiketleyici Local CA")]
        )
        now = datetime.now(timezone.utc)
        ca_certificate = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=None,
                    decipher_only=None,
                ),
                critical=True,
            )
            .sign(ca_key, hashes.SHA256())
        )
        _write_private_key(
            ca_key_path,
            ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ),
        )
        ca_certificate_path.write_bytes(
            ca_certificate.public_bytes(serialization.Encoding.PEM)
        )

    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "Filament Etiketleyici")]
    )
    san_entries = [x509.DNSName(name) for name in set(dns_names)]
    san_entries.extend(
        x509.IPAddress(ipaddress.ip_address(address))
        for address in set(ip_addresses)
    )
    now = datetime.now(timezone.utc)
    server_certificate = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_certificate.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=397))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    _write_private_key(
        server_key_path,
        server_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
    )
    server_certificate_path.write_bytes(
        server_certificate.public_bytes(serialization.Encoding.PEM)
    )
    return LocalCertificateFiles(
        ca_certificate=ca_certificate_path,
        server_certificate=server_certificate_path,
        server_key=server_key_path,
        ca_fingerprint=ca_certificate.fingerprint(hashes.SHA256()).hex(":"),
    )


def _write_private_key(path: Path, key_bytes: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "wb") as key_file:
        key_file.write(key_bytes)


def _public_key_bytes(public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

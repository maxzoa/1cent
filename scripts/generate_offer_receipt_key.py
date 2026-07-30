import argparse
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from onecent.services.offer_receipt import OfferReceiptSigner, did_document


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a dedicated 1cent receipt signing key")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--kid", default="did:web:1cent.maxzoa.ru#offer-receipt-key-1"
    )
    parser.add_argument("--owner-uid", type=int)
    parser.add_argument("--owner-gid", type=int)
    args = parser.parse_args()
    if (args.owner_uid is None) != (args.owner_gid is None):
        raise SystemExit("--owner-uid and --owner-gid must be provided together")
    output = Path(args.output).resolve()
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit("refusing to overwrite existing signing key")
    key = Ed25519PrivateKey.generate()
    output.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    os.chmod(output, 0o600)
    if args.owner_uid is not None and args.owner_gid is not None:
        os.chown(output, args.owner_uid, args.owner_gid)
    signer = OfferReceiptSigner.load(str(output), args.kid)
    print(json.dumps(did_document(signer), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

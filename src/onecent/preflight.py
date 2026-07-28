import argparse

from pydantic import ValidationError

from onecent.config import Settings
from onecent.services.readiness import backup_age_hours, mainnet_blockers, short_address


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only 1cent mainnet readiness check")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    try:
        settings = Settings(_env_file=args.env_file)  # type: ignore[call-arg]
    except ValidationError as exc:
        print("production_ready=no")
        for error in exc.errors(include_url=False, include_input=False):
            print(f"BLOCKER: {error['msg']}")
        return 1

    blockers = mainnet_blockers(settings)
    age = backup_age_hours(settings.mainnet_backup_path)
    print("production_ready=" + ("yes" if not blockers else "no"))
    print(f"profile={settings.deployment_profile}")
    print(f"network={settings.x402_network}")
    print(f"seller={short_address(settings.x402_pay_to)}")
    print(f"mainnet_approval={settings.owner_mainnet_approved}")
    print(f"backup_age_hours={'missing' if age is None else f'{age:.1f}'}")
    for blocker in blockers:
        print(f"BLOCKER: {blocker}")
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())

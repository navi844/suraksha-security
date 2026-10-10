from __future__ import annotations

import argparse
import json

from audit_log import audit_log


def main() -> int:
    parser = argparse.ArgumentParser(description='Query the local Suraksha audit log')
    parser.add_argument('--event-type', default=None)
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    rows = audit_log.query(event_type=args.event_type, limit=args.limit)
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

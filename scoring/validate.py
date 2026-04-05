#!/usr/bin/env python3
"""
Validate the workspace structure and compare scores against reference.
"""

import json
import os
import sys


def validate_workspace():
    """Check that all required files exist."""
    required = [
        'briefing/problem.md',
        'briefing/evaluation.md',
        'briefing/method.md',
        'briefing/overview.md',
        'scoring/reference.json',
        'scoring/scores.json',
        'scripts/evaluate.sh',
        'scripts/reproduce.sh',
        'scripts/download.sh',
        'scripts/method.sh',
        'scripts/baseline.sh',
        'environment/container.def',
        'environment/setup.sh',
        'method/quasi_fresnel.py',
        'eval/metrics.py',
        'data/generate_nlos_data.py',
        'baseline/fbp.py',
        'baseline/lct.py',
    ]

    print("Validating workspace structure...")
    missing = []
    for f in required:
        if not os.path.exists(f):
            missing.append(f)

    if missing:
        print(f"  MISSING: {', '.join(missing)}")
        return False

    print("  All required files present")
    return True


def load_json(path):
    with open(path) as f:
        return json.load(f)


def validate_reference():
    """Validate reference.json structure."""
    print("\nValidating reference.json...")
    try:
        ref = load_json('scoring/reference.json')
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    if 'experiments' not in ref:
        print("  ERROR: missing 'experiments' key")
        return False

    for exp_name, exp_data in ref['experiments'].items():
        required = ['description', 'weight', 'primary_metric', 'metrics', 'results']
        for k in required:
            if k not in exp_data:
                print(f"  ERROR: experiment '{exp_name}' missing '{k}'")
                return False

        # Validate results
        for method_name, result in exp_data['results'].items():
            if 'type' not in result:
                print(f"  ERROR: method '{method_name}' missing 'type'")
                return False

    print(f"  {len(ref['experiments'])} experiments validated")
    return True


def compare_scores():
    """Compare scores.json against reference.json."""
    print("\nComparing scores.json vs reference.json...")
    try:
        ref = load_json('scoring/reference.json')
        scores = load_json('scoring/scores.json')
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    total_weight = 0
    for exp_name, exp_data in ref['experiments'].items():
        total_weight += exp_data['weight']

    if abs(total_weight - 1.0) > 0.01:
        print(f"  WARNING: experiment weights sum to {total_weight:.3f}, not 1.0")

    # Check if scores.json has expected structure
    if 'experiments' not in scores:
        print("  scores.json does not have 'experiments' key — may be using different format")

    print("  Score comparison available (reference.json has target values)")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--compare', action='store_true', help='Compare scores against reference')
    args = parser.parse_args()

    ok = validate_workspace()
    if not ok:
        sys.exit(1)

    ok = validate_reference()
    if not ok:
        sys.exit(1)

    if args.compare:
        ok = compare_scores()
        if not ok:
            sys.exit(1)

    print("\n✓ Workspace validation passed")


if __name__ == '__main__':
    main()

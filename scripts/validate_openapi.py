#!/usr/bin/env python3
"""
Validate OpenAPI specification

This script validates the OpenAPI spec for correctness.
Requires: pip install openapi-spec-validator
"""

import sys
from pathlib import Path

try:
    from openapi_spec_validator import validate_spec
    from openapi_spec_validator.readers import read_from_filename
except ImportError:
    print("ERROR: openapi-spec-validator not installed")
    print("Install with: pip install openapi-spec-validator")
    sys.exit(1)


def validate_openapi_spec(spec_path: Path) -> bool:
    """
    Validate OpenAPI specification file.

    Args:
        spec_path: Path to the OpenAPI spec file (YAML or JSON)

    Returns:
        True if valid, False otherwise
    """
    try:
        print(f"Validating OpenAPI spec: {spec_path}")
        print("=" * 60)

        # Read and parse the spec
        spec_dict, spec_url = read_from_filename(str(spec_path))

        # Validate the spec
        validate_spec(spec_dict)

        print("✓ OpenAPI specification is valid!")
        print()
        print("Specification Details:")
        print(f"  Title: {spec_dict['info']['title']}")
        print(f"  Version: {spec_dict['info']['version']}")
        print(f"  OpenAPI Version: {spec_dict['openapi']}")

        if 'paths' in spec_dict:
            print(f"  Endpoints: {len(spec_dict['paths'])}")
            print()
            print("  Available Endpoints:")
            for path in spec_dict['paths']:
                methods = list(spec_dict['paths'][path].keys())
                print(f"    {path} [{', '.join(methods).upper()}]")

        if 'components' in spec_dict and 'schemas' in spec_dict['components']:
            schemas = spec_dict['components']['schemas']
            print(f"\n  Schemas: {len(schemas)}")

        print()
        print("=" * 60)
        print("✓ Validation successful!")
        return True

    except Exception as e:
        print(f"\n✗ Validation failed!")
        print(f"Error: {e}")
        print()
        return False


def main():
    """Main entry point"""
    # Get spec path
    repo_root = Path(__file__).parent.parent
    spec_path = repo_root / "docs" / "openapi" / "mt5-api-spec.yaml"

    if not spec_path.exists():
        print(f"ERROR: Spec file not found: {spec_path}")
        sys.exit(1)

    # Validate
    success = validate_openapi_spec(spec_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

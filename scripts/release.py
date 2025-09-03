#!/usr/bin/env python3
"""
Release script for NGBSE 20.2.0-GA.
Automates the release process with validation and safety checks.
"""
import argparse
import subprocess
import sys
from typing import List
import re


def run_command(cmd: List[str], capture_output: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        if capture_output and e.stdout:
            print(f"STDOUT: {e.stdout}")
        if capture_output and e.stderr:
            print(f"STDERR: {e.stderr}")
        sys.exit(1)


def check_git_status() -> bool:
    """Check if git repository is clean."""
    result = run_command(["git", "status", "--porcelain"])
    if result.stdout.strip():
        print("❌ Git repository is not clean. Please commit or stash changes.")
        print("Uncommitted changes:")
        print(result.stdout)
        return False
    print("✅ Git repository is clean")
    return True


def check_branch() -> str:
    """Check current git branch."""
    result = run_command(["git", "branch", "--show-current"])
    branch = result.stdout.strip()
    print(f"Current branch: {branch}")
    return branch


def run_tests() -> bool:
    """Run all tests."""
    print("🧪 Running tests...")
    try:
        run_command(["make", "test"])
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        return False


def run_security_checks() -> bool:
    """Run security checks."""
    print("🔒 Running security checks...")
    try:
        run_command(["make", "security"])
        print("✅ Security checks passed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Security checks failed")
        return False


def run_linting() -> bool:
    """Run linting and formatting checks."""
    print("🔍 Running linting...")
    try:
        run_command(["make", "format"])
        run_command(["make", "lint"])
        run_command(["make", "type"])
        print("✅ Linting passed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Linting failed")
        return False


def generate_sbom() -> bool:
    """Generate SBOM."""
    print("📦 Generating SBOM...")
    try:
        run_command(["make", "sbom"])
        print("✅ SBOM generated")
        return True
    except subprocess.CalledProcessError:
        print("❌ SBOM generation failed")
        return False


def check_version_consistency() -> bool:
    """Check that version is consistent across files."""
    print("🔢 Checking version consistency...")

    # Read version from pyproject.toml
    with open("pyproject.toml", "r") as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if not match:
            print("❌ Could not find version in pyproject.toml")
            return False
        version = match.group(1)

    print(f"Version in pyproject.toml: {version}")

    # Check if version follows expected pattern
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"❌ Version {version} does not follow semantic versioning")
        return False

    # Check CHANGELOG.md
    with open("CHANGELOG.md", "r") as f:
        changelog = f.read()
        if f"[{version}]" not in changelog:
            print(f"❌ Version {version} not found in CHANGELOG.md")
            return False

    print("✅ Version consistency check passed")
    return True


def create_release_commit(version: str) -> bool:
    """Create release commit."""
    print(f"📝 Creating release commit for {version}...")

    commit_message = f"Release {version}: Complete modular architecture with enhanced security"

    try:
        run_command(["git", "add", "."])
        run_command(["git", "commit", "-m", commit_message])
        print("✅ Release commit created")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create release commit")
        return False


def create_release_tag(version: str) -> bool:
    """Create release tag."""
    print(f"🏷️ Creating release tag v{version}...")

    tag_message = f"NGBSE {version} Release"

    try:
        run_command(["git", "tag", "-a", f"v{version}", "-m", tag_message])
        print("✅ Release tag created")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create release tag")
        return False


def push_release(branch: str, version: str) -> bool:
    """Push release to remote."""
    print(f"🚀 Pushing release to remote...")

    try:
        run_command(["git", "push", "origin", branch])
        run_command(["git", "push", "origin", f"v{version}"])
        print("✅ Release pushed to remote")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to push release")
        return False


def validate_release() -> bool:
    """Run all validation checks."""
    print("🔍 Running release validation...")

    checks = [
        ("Git Status", check_git_status),
        ("Tests", run_tests),
        ("Security", run_security_checks),
        ("Linting", run_linting),
        ("SBOM Generation", generate_sbom),
        ("Version Consistency", check_version_consistency),
    ]

    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        if not check_func():
            print(f"❌ {check_name} failed")
            return False

    print("\n✅ All validation checks passed!")
    return True


def get_version() -> str:
    """Get current version from pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")


def main():
    """Main release function."""
    parser = argparse.ArgumentParser(description="Release NGBSE 20.2.0-GA")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only run validation, don't create release")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip validation checks")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without executing")

    args = parser.parse_args()

    version = get_version()
    branch = check_branch()

    print(f"🚀 NGBSE Release Process")
    print(f"Version: {version}")
    print(f"Branch: {branch}")
    print(f"Dry run: {args.dry_run}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        print("Would execute:")
        print("1. Validation checks")
        print("2. Create release commit")
        print("3. Create release tag")
        print("4. Push to remote")
        return

    # Run validation unless skipped
    if not args.skip_validation:
        if not validate_release():
            print("❌ Validation failed. Release aborted.")
            sys.exit(1)

    if args.validate_only:
        print("✅ Validation complete. Use --skip-validation to create release.")
        return

    # Create release
    print(f"\n🎯 Creating release {version}...")

    if not create_release_commit(version):
        print("❌ Failed to create release commit")
        sys.exit(1)

    if not create_release_tag(version):
        print("❌ Failed to create release tag")
        sys.exit(1)

    if not push_release(branch, version):
        print("❌ Failed to push release")
        sys.exit(1)

    print(f"\n🎉 Release {version} created successfully!")
    print(f"Tag: v{version}")
    print(f"Branch: {branch}")
    print("\nNext steps:")
    print("1. Create GitHub release from tag")
    print("2. Upload SBOM files")
    print("3. Upload Docker image")
    print("4. Notify stakeholders")


if __name__ == "__main__":
    main()

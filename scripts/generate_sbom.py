#!/usr/bin/env python3
"""
SBOM (Software Bill of Materials) generation script for NGBSE 20.2.
Generates CycloneDX and SPDX format SBOMs for supply chain security.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_command(
    cmd: list[str], capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        sys.exit(1)


def check_syft_installed() -> bool:
    """Check if Syft is installed."""
    try:
        run_command(["syft", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_syft() -> None:
    """Install Syft if not available."""
    print("Installing Syft...")
    install_cmd = [
        "curl",
        "-sSfL",
        "https://raw.githubusercontent.com/anchore/syft/main/install.sh",
    ]

    try:
        # Download and install Syft
        result = subprocess.run(
            install_cmd + ["|", "sh", "-s", "--", "-b", "/usr/local/bin"],
            shell=True,
            check=True,
        )
        print("Syft installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Syft: {e}")
        print("Please install Syft manually: https://github.com/anchore/syft")
        sys.exit(1)


def generate_cyclonedx_sbom(output_file: str) -> None:
    """Generate CycloneDX format SBOM."""
    print(f"Generating CycloneDX SBOM: {output_file}")

    cmd = ["syft", "packages", ".", "-o", "cyclonedx-json", "--file", output_file]

    run_command(cmd)
    print(f"CycloneDX SBOM saved to {output_file}")


def generate_spdx_sbom(output_file: str) -> None:
    """Generate SPDX format SBOM."""
    print(f"Generating SPDX SBOM: {output_file}")

    cmd = ["syft", "packages", ".", "-o", "spdx-json", "--file", output_file]

    run_command(cmd)
    print(f"SPDX SBOM saved to {output_file}")


def generate_python_sbom(output_file: str) -> None:
    """Generate Python-specific SBOM using pip-tools."""
    print(f"Generating Python SBOM: {output_file}")

    try:
        # Try to use pip-tools if available
        result = run_command(["pip", "list", "--format=json"])
        packages = json.loads(result.stdout)

        # Convert to CycloneDX format
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "metadata": {
                "timestamp": "2024-01-01T00:00:00Z",
                "tools": [
                    {"vendor": "NGBSE", "name": "SBOM Generator", "version": "20.2.0"}
                ],
                "component": {
                    "type": "application",
                    "name": "NGBSE",
                    "version": "20.2.0-GA",
                    "description": "Next-Generation Business Security Engine",
                },
            },
            "components": [],
        }

        for package in packages:
            component = {
                "type": "library",
                "name": package["name"],
                "version": package["version"],
                "purl": f"pkg:pypi/{package['name']}@{package['version']}",
            }
            sbom["components"].append(component)

        with open(output_file, "w") as f:
            json.dump(sbom, f, indent=2)

        print(f"Python SBOM saved to {output_file}")

    except Exception as e:
        print(f"Failed to generate Python SBOM: {e}")


def validate_sbom(sbom_file: str) -> bool:
    """Validate SBOM file format."""
    try:
        with open(sbom_file) as f:
            data = json.load(f)

        # Basic validation
        if "bomFormat" in data and data["bomFormat"] == "CycloneDX":
            print(f"✓ {sbom_file} is valid CycloneDX format")
            return True
        elif "spdxVersion" in data:
            print(f"✓ {sbom_file} is valid SPDX format")
            return True
        else:
            print(f"✗ {sbom_file} format not recognized")
            return False

    except Exception as e:
        print(f"✗ Failed to validate {sbom_file}: {e}")
        return False


def generate_sbom_summary(sbom_files: list[str], output_file: str) -> None:
    """Generate a summary of all SBOMs."""
    summary = {
        "generated_at": "2024-01-01T00:00:00Z",
        "ngbse_version": "20.2.0-GA",
        "sbom_files": [],
        "total_components": 0,
        "formats": [],
    }

    for sbom_file in sbom_files:
        if Path(sbom_file).exists():
            try:
                with open(sbom_file) as f:
                    data = json.load(f)

                file_info = {
                    "file": sbom_file,
                    "format": data.get("bomFormat", "SPDX"),
                    "components": len(data.get("components", [])),
                    "valid": True,
                }

                summary["sbom_files"].append(file_info)
                summary["total_components"] += file_info["components"]

                if file_info["format"] not in summary["formats"]:
                    summary["formats"].append(file_info["format"])

            except Exception as e:
                file_info = {
                    "file": sbom_file,
                    "format": "unknown",
                    "components": 0,
                    "valid": False,
                    "error": str(e),
                }
                summary["sbom_files"].append(file_info)

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"SBOM summary saved to {output_file}")


def main():
    """Main SBOM generation function."""
    parser = argparse.ArgumentParser(description="Generate SBOM for NGBSE 20.2")
    parser.add_argument(
        "--output-dir", default=".", help="Output directory for SBOM files"
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["cyclonedx", "spdx", "python", "all"],
        default=["all"],
        help="SBOM formats to generate",
    )
    parser.add_argument(
        "--install-syft", action="store_true", help="Install Syft if not available"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate generated SBOMs"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Check if Syft is available
    if not check_syft_installed():
        if args.install_syft:
            install_syft()
        else:
            print("Syft not found. Use --install-syft to install it automatically.")
            print("Or install manually: https://github.com/anchore/syft")
            sys.exit(1)

    sbom_files = []

    # Generate SBOMs based on requested formats
    if "all" in args.formats or "cyclonedx" in args.formats:
        cyclonedx_file = output_dir / "sbom-cyclonedx.json"
        generate_cyclonedx_sbom(str(cyclonedx_file))
        sbom_files.append(str(cyclonedx_file))

    if "all" in args.formats or "spdx" in args.formats:
        spdx_file = output_dir / "sbom-spdx.json"
        generate_spdx_sbom(str(spdx_file))
        sbom_files.append(str(spdx_file))

    if "all" in args.formats or "python" in args.formats:
        python_file = output_dir / "sbom-python.json"
        generate_python_sbom(str(python_file))
        sbom_files.append(str(python_file))

    # Validate SBOMs if requested
    if args.validate:
        print("\nValidating SBOMs...")
        for sbom_file in sbom_files:
            validate_sbom(sbom_file)

    # Generate summary
    summary_file = output_dir / "sbom-summary.json"
    generate_sbom_summary(sbom_files, str(summary_file))

    print("\n✓ SBOM generation complete!")
    print(f"Generated {len(sbom_files)} SBOM files in {output_dir}")
    print(f"Summary: {summary_file}")


if __name__ == "__main__":
    main()

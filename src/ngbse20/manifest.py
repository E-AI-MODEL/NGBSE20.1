import hashlib
import json
import time


def sha256_file(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None

def write_manifest(out_dir: str, version: str, seeds_path: str, config_path: str, findings_path: str) -> None:
    start_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    time.sleep(1) # Simulate work
    end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    manifest = {
        "ngbse_version": version,
        "start_time": start_time,
        "end_time": end_time,
        "hashes": {
            "seeds.jsonl": sha256_file(seeds_path),
            "ngbse.config.yml": sha256_file(config_path),
            "findings.jsonl": sha256_file(findings_path)
        }
    }
    with open(f"{out_dir}/MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

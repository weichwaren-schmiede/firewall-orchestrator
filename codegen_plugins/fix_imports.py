import re
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
content = PYPROJECT.read_text()

package_name_match = re.search(r'target_package_name\s*=\s*"([^"]+)"', content)
package_path_match = re.search(r'target_package_path\s*=\s*"([^"]+)"', content)

if not package_name_match:
    raise ValueError("target_package_name not found in pyproject.toml")

package_name = package_name_match.group(1)
package_path = Path(package_path_match.group(1) if package_path_match else ".")

output_dir = package_path / package_name
package_prefix = ".".join([*package_path.parts, package_name])

for file in output_dir.glob("*.py"):
    original = file.read_text()
    fixed = re.sub(
        r"from \.([\w]+) import",
        lambda m: f"from {package_prefix}.{m.group(1)} import",
        original,
    )
    if fixed != original:
        file.write_text(fixed)
        print(f"Fixed: {file.name}") # noqa: T201

print(f"Done. Processed {output_dir}")  # noqa: T201

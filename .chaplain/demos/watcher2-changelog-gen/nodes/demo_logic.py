import os
import re
from pathlib import Path


def demo_fr283_logic(state):
    """
    FR-283 Changelog Fragment Auto-Generation Demo
    Simulates the logic added to watcher2.sh
    """

    output = []
    output.append("=== FR-283 Demo: Changelog Fragment Auto-Generation ===")

    fr_path = state["fr_path"]
    output.append(f"FR_PATH: {fr_path}")
    output.append("")

    # Extract FR number from feature request path
    fr_num_match = re.search(r"FR-(\d+)", fr_path)
    if fr_num_match:
        fr_num = fr_num_match.group(1)
        fr_id = f"FR-{fr_num}"
        output.append(f"Extracted FR number: {fr_num}")
        output.append(f"FR ID: {fr_id}")
        output.append("")

        # Generate changelog fragment filename
        basename = Path(fr_path).stem
        descriptive = re.sub(rf"^FR-{fr_num}-", "", basename)
        descriptive = descriptive[:40]  # Truncate to 40 chars
        changelog_frag = f"tmp/demo-changelog/unreleased/fr-{fr_num}-{descriptive}.md"
        output.append(f"Generated fragment path: {changelog_frag}")
        output.append("")

        # Derive change type and scope from FR path
        change_type = "feat"
        scope = descriptive.split("-")[0] if descriptive else "watcher"
        output.append(f"Change type: {change_type}")
        output.append(f"Scope: {scope}")
        output.append("")

        # Simulate requirement lookup
        output.append("🔍 Looking up REQ-YG-XXX from capabilities registry...")
        req_id = "REQ-YG-162"  # Simulated lookup result
        output.append(f"✅ Found requirement: {req_id}")
        output.append("")

        # FR number validation
        expected_fr_num = re.search(r"(\d+)", fr_path).group(1)
        if fr_num == expected_fr_num:
            output.append("✅ FR number validation passed")
        else:
            output.append(f"⚠️  FR number mismatch: {fr_num} vs {expected_fr_num}")
        output.append("")

        # Generate fragment content
        output.append("📝 Generating changelog fragment...")
        os.makedirs("tmp/demo-changelog/unreleased", exist_ok=True)

        fragment_content = "---\n"
        fragment_content += f"type: {change_type}\n"
        fragment_content += f"scope: {scope}\n"
        fragment_content += f"req: {req_id}\n"
        fragment_content += "---\n"
        fragment_content += (
            f"- **{fr_id}**: Auto-generated changelog fragment demo. ({req_id})"
        )

        with open(changelog_frag, "w", encoding="utf-8") as f:
            f.write(fragment_content)

        output.append(f"✅ Generated changelog fragment: {changelog_frag}")
        output.append("")
        output.append("Fragment content:")
        output.append(fragment_content)
    else:
        output.append("❌ Failed to extract FR number from path")

    output.append("")
    output.append("=== Demo Complete ===")

    return {"demo_output": "\n".join(output)}

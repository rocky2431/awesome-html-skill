"""Check the portable plugin surface; native loading and behavior are separate."""

import json
import re
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    plugin = root / "plugins" / "awesome-html"
    skill = plugin / "skills" / "awesome-html"
    manifest_paths = [
        plugin / ".codex-plugin" / "plugin.json",
        plugin / ".claude-plugin" / "plugin.json",
        plugin / ".zcode-plugin" / "plugin.json",
        plugin / "kimi.plugin.json",
    ]
    manifests = [json.loads(path.read_text()) for path in manifest_paths]
    version = manifests[0]["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
    for path, manifest in zip(manifest_paths, manifests):
        assert manifest["name"] == plugin.name, path
        assert manifest["version"] == version, path
        assert manifest["description"] == manifests[0]["description"], path
        assert not {"hooks", "commands", "mcpServers", "apps"} & manifest.keys(), path
    assert manifests[0]["skills"] == "./skills/"
    assert manifests[2]["skills"] == "skills"
    assert manifests[3]["skills"] == ["./skills"]
    assert list(plugin.rglob("SKILL.md")) == [skill / "SKILL.md"]
    entry = (skill / "SKILL.md").read_text()
    assert re.search(r"(?m)^name: awesome-html$", entry)
    description = re.search(r"(?m)^description: (.+)$", entry).group(1)
    assert len(description) <= 1024, len(description)

    codex_catalog = json.loads((root / ".agents/plugins/marketplace.json").read_text())
    claude_catalog = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    assert codex_catalog["name"] == claude_catalog["name"] == "rocky-awesome-html"
    for catalog in (codex_catalog, claude_catalog):
        assert [item["name"] for item in catalog["plugins"]] == [plugin.name]
    assert codex_catalog["plugins"][0]["source"]["path"] == "./plugins/awesome-html"
    assert claude_catalog["plugins"][0]["source"] == "./plugins/awesome-html"
    assert "version" not in claude_catalog["metadata"]
    assert "version" not in claude_catalog["plugins"][0]

    # Every file SKILL.md points at exists.
    for target in re.findall(r"`((?:references|assets|scripts)/[\w./-]+)`", entry):
        if "<" not in target:
            assert (skill / target).exists(), target

    for path in [*plugin.rglob("*"), *root.glob("*.md"), *(root / "docs").rglob("*.md")]:
        assert not path.is_symlink(), path
        if not path.is_file() or path.name == ".DS_Store" or "__pycache__" in path.parts:
            continue
        assert path.suffix in {".md", ".json", ".yaml", ".py", ".html", ".js"}, path
        body = path.read_text(encoding="utf-8")
        assert body.endswith("\n") or path.parent.name == "vendor", path
        assert "/Users/" not in body and "/var/folders/" not in body, path
        if path.parent.name == "vendor":
            continue
        assert all(line == line.rstrip() for line in body.splitlines()), path
        if path.suffix != ".md":
            continue
        for target in re.findall(r"\]\(([^)]+)\)", body):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            relative = target.split("#", 1)[0]
            assert (path.parent / relative).exists(), f"{path}: broken link {target}"
    print("package ok", version)


if __name__ == "__main__":
    main()

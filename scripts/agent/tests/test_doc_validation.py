from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("agent_tool", ROOT / "scripts/agent/agent_tool.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)

def test_template_headings():
    spec_text = (ROOT / "docs/templates/spec-template.md").read_text(encoding="utf-8")
    design_text = (ROOT / "docs/templates/design-template.md").read_text(encoding="utf-8")
    spec_heads = module.markdown_headings(spec_text)
    design_heads = module.markdown_headings(design_text)
    assert not (set(module.SPEC_REQUIRED) - spec_heads)
    assert not (set(module.DESIGN_REQUIRED) - design_heads)

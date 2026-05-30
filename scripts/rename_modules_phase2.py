"""Phase-2 rename: remaining generic module names (exact dotted-path replacements)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "src" / "iapetus"

# Longest paths first when applying text replacements.
REPLACEMENTS: list[tuple[str, str]] = [
    ("iapetus.cli.learning_concept_handlers", "iapetus.cli.curated_concept_learning_handlers"),
    ("iapetus.cli.learning_handlers_compat", "iapetus.cli.learning_subcommand_handler_bridge"),
    ("iapetus.cli.learning_training_handlers", "iapetus.cli.static_mlp_smoke_training_handlers"),
    ("iapetus.cli.learning_console_dispatch", "iapetus.cli.interactive_learning_console_router"),
    ("iapetus.cli.learning_registry_output", "iapetus.cli.sqlite_learning_index_cli_output"),
    ("iapetus.cli.learning_commands", "iapetus.cli.typer_learning_command_group"),
    ("iapetus.cli.bad_data_handlers", "iapetus.cli.adversarial_validation_handlers"),
    ("iapetus.cli.bad_data_commands", "iapetus.cli.typer_adversarial_validation_commands"),
    ("iapetus.cli.operator_menu", "iapetus.cli.interactive_operator_menu"),
    ("iapetus.cli.shared_utilities", "iapetus.cli.cli_console_and_path_helpers"),
    ("iapetus.data_library", "iapetus.curated_seed_library_exports"),
    ("iapetus.project_filesystem_paths", "iapetus.project_filesystem_paths"),  # idempotent guard
    ("iapetus.paths", "iapetus.project_filesystem_paths"),
    ("iapetus.application_config", "iapetus.application_config"),
    ("iapetus.config", "iapetus.application_config"),
    ("iapetus.knowledge.knowledge_artifact_registry", "iapetus.knowledge.knowledge_artifact_registry"),
    ("iapetus.knowledge.registry", "iapetus.knowledge.knowledge_artifact_registry"),
    ("iapetus.knowledge.android_platform_concepts", "iapetus.knowledge.android_platform_concepts"),
    ("iapetus.knowledge.android", "iapetus.knowledge.android_platform_concepts"),
    ("iapetus.knowledge.apk_anatomy_reference", "iapetus.knowledge.apk_anatomy_reference"),
    ("iapetus.knowledge.apk", "iapetus.knowledge.apk_anatomy_reference"),
    ("iapetus.knowledge.synthetic_android_samples", "iapetus.knowledge.synthetic_android_samples"),
    ("iapetus.knowledge.fake", "iapetus.knowledge.synthetic_android_samples"),
    ("iapetus.connectors.external_connector_catalog", "iapetus.connectors.external_connector_catalog"),
    ("iapetus.connectors.registry", "iapetus.connectors.external_connector_catalog"),
    ("iapetus.labels.structured_malware_label_schema", "iapetus.labels.structured_malware_label_schema"),
    ("iapetus.labels.schema", "iapetus.labels.structured_malware_label_schema"),
    ("iapetus.labels.malware_label_text_renderer", "iapetus.labels.malware_label_text_renderer"),
    ("iapetus.labels.renderer", "iapetus.labels.malware_label_text_renderer"),
]

FILE_RENAMES: list[tuple[str, str]] = [
    ("config.py", "application_config.py"),
    ("paths.py", "project_filesystem_paths.py"),
    ("data_library.py", "curated_seed_library_exports.py"),
    ("cli/bad_data_handlers.py", "cli/adversarial_validation_handlers.py"),
    ("cli/learning_concept_handlers.py", "cli/curated_concept_learning_handlers.py"),
    ("cli/learning_handlers_compat.py", "cli/learning_subcommand_handler_bridge.py"),
    ("cli/learning_training_handlers.py", "cli/static_mlp_smoke_training_handlers.py"),
    ("cli/learning_console_dispatch.py", "cli/interactive_learning_console_router.py"),
    ("cli/learning_registry_output.py", "cli/sqlite_learning_index_cli_output.py"),
    ("cli/operator_menu.py", "cli/interactive_operator_menu.py"),
    ("cli/shared_utilities.py", "cli/cli_console_and_path_helpers.py"),
    ("cli/learning_commands.py", "cli/typer_learning_command_group.py"),
    ("cli/bad_data_commands.py", "cli/typer_adversarial_validation_commands.py"),
    ("connectors/registry.py", "connectors/external_connector_catalog.py"),
    ("knowledge/android.py", "knowledge/android_platform_concepts.py"),
    ("knowledge/apk.py", "knowledge/apk_anatomy_reference.py"),
    ("knowledge/fake.py", "knowledge/synthetic_android_samples.py"),
    ("knowledge/registry.py", "knowledge/knowledge_artifact_registry.py"),
    ("labels/schema.py", "labels/structured_malware_label_schema.py"),
    ("labels/renderer.py", "labels/malware_label_text_renderer.py"),
]

RELATIVE_PATCHES: dict[str, list[tuple[str, str]]] = {
    "knowledge/knowledge_artifact_registry.py": [
        ("from .android import", "from .android_platform_concepts import"),
        ("from .apk import", "from .apk_anatomy_reference import"),
    ],
    "knowledge/__init__.py": [
        ("from .android import", "from .android_platform_concepts import"),
        ("from .registry import", "from .knowledge_artifact_registry import"),
        ("from .apk import", "from .apk_anatomy_reference import"),
        ("from .fake import", "from .synthetic_android_samples import"),
    ],
    "connectors/__init__.py": [
        ("from .registry import", "from .external_connector_catalog import"),
    ],
    "labels/__init__.py": [
        ("from .renderer import", "from .malware_label_text_renderer import"),
    ],
    "labels/malware_label_text_renderer.py": [
        ("from .schema import", "from .structured_malware_label_schema import"),
    ],
}


def rename_files() -> None:
    for old, new in FILE_RENAMES:
        src = BASE / old
        dst = BASE / new
        if not src.is_file():
            raise FileNotFoundError(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        print(f"renamed {old} -> {new}")


def apply_replacements(text: str) -> str:
    ordered = sorted(REPLACEMENTS, key=lambda x: len(x[0]), reverse=True)
    for old, new in ordered:
        if old != new:
            text = text.replace(old, new)
    # ``from iapetus import paths`` after paths module rename
    text = text.replace(
        "from iapetus import project_filesystem_paths",
        "from iapetus import project_filesystem_paths",
    )
    text = text.replace("from iapetus import paths", "from iapetus import project_filesystem_paths as paths")
    text = text.replace("import iapetus.paths as paths", "import iapetus.project_filesystem_paths as paths")
    return text


def main() -> None:
    rename_files()
    patched = 0
    for path in ROOT.rglob("*"):
        if path.suffix not in {".py", ".md"}:
            continue
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        if path.name == "rename_modules_phase2.py":
            continue
        text = path.read_text(encoding="utf-8")
        new_text = apply_replacements(text)
        if path.is_relative_to(BASE):
            rel = path.relative_to(BASE).as_posix()
            for old, new in RELATIVE_PATCHES.get(rel, []):
                new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            patched += 1
            print(f"patched {path.relative_to(ROOT)}")
    print(f"done: {patched} files")


if __name__ == "__main__":
    main()

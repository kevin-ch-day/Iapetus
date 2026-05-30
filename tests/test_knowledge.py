from __future__ import annotations

from typer.testing import CliRunner

from iapetus.cli import app
from iapetus.knowledge import get_dataset_row_count, list_fake_topics, run_concepts
from iapetus.knowledge.registry import ArtifactClassifier, classify_artifact


def test_concept_registry_contains_core_android_concepts() -> None:
    concept_ids = {concept.concept_id for concept in run_concepts()}
    assert "android" in concept_ids
    assert "android_app" in concept_ids
    assert "apk" in concept_ids
    assert "aab" in concept_ids
    assert "android_manifest" in concept_ids
    assert "permission_model" in concept_ids
    assert "android_runtime" in concept_ids
    assert "apk_signing" in concept_ids
    assert "android_components" in concept_ids


def test_apk_concept_includes_manifest_and_classes() -> None:
    artifact_types = {concept.concept_id: concept for concept in run_concepts()}
    apk_concept = artifact_types["apk"]
    assert "AndroidManifest.xml" in apk_concept.key_fields
    assert "classes.dex" in apk_concept.key_fields


def test_artifact_classify_apk_extension() -> None:
    classification = ArtifactClassifier.classify("sample.apk")
    assert classification.artifact_type == "Android APK"
    assert classification.normalized_extension == ".apk"


def test_artifact_classify_uppercase_apk_extension() -> None:
    classification = ArtifactClassifier.classify("SAMPLE.APK")
    assert classification.artifact_type == "Android APK"
    assert classification.normalized_extension == ".apk"


def test_artifact_classify_aab_extension() -> None:
    classification = ArtifactClassifier.classify("bundle.aab")
    assert classification.artifact_type == "Android AAB"
    assert classification.normalized_extension == ".aab"


def test_artifact_classify_exe_extension() -> None:
    classification = classify_artifact("malware.exe")
    assert classification.artifact_type == "Windows PE"
    assert classification.normalized_extension == ".exe"


def test_artifact_classify_unknown_extension() -> None:
    classification = classify_artifact("README.notes")
    assert classification.artifact_type == "Unknown"


def test_android_apk_is_permission_analysis_eligible() -> None:
    classification = classify_artifact("sample.apk")
    assert classification.relevance.eligible_for_android_permission_analysis is True


def test_windows_exe_not_android_permission_eligible() -> None:
    classification = classify_artifact("malware.exe")
    assert classification.relevance.eligible_for_android_permission_analysis is False


def test_artifact_classify_ps1_and_so_extensions() -> None:
    ps1_classification = classify_artifact("script.ps1")
    so_classification = classify_artifact("libnative.so")
    sh_classification = classify_artifact("tools.sh")

    assert ps1_classification.artifact_type == "Windows PowerShell Script"
    assert so_classification.artifact_type == "Linux/Unix Artifact"
    assert sh_classification.artifact_type == "Linux/Unix Artifact"
    assert not ps1_classification.relevance.eligible_for_android_permission_analysis
    assert not ps1_classification.relevance.eligible_for_windows_pe_analysis


def test_artifact_classify_query_like_paths() -> None:
    classification = classify_artifact("sample.apk?download=true")
    assert classification.artifact_type == "Android APK"


def test_artifact_classify_non_file_like_path() -> None:
    classification = classify_artifact("artifacts/folder/")  
    assert classification.artifact_type == "Unknown"
    assert classification.normalized_extension == ""


def test_knowledge_cli_concepts_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "concepts"])
    assert result.exit_code == 0
    assert "Knowledge concepts" in result.stdout
    assert "android" in result.stdout
    assert "apk" in result.stdout


def test_knowledge_cli_show_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "apk"])
    assert result.exit_code == 0
    assert "Android app artifact" in result.stdout
    assert "AndroidManifest.xml" in result.stdout


def test_knowledge_cli_show_android_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android"])
    assert result.exit_code == 0
    assert "Mobile operating system" in result.stdout


def test_knowledge_cli_show_android_app_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android_app"])
    assert result.exit_code == 0
    assert "Android app package" in result.stdout


def test_knowledge_cli_show_android_manifest_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android_manifest"])
    assert result.exit_code == 0
    assert "AndroidManifest schema" in result.stdout


def test_knowledge_cli_show_permission_model_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "permission_model"])
    assert result.exit_code == 0
    assert "Android permission model" in result.stdout


def test_knowledge_cli_show_android_runtime_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android_runtime"])
    assert result.exit_code == 0
    assert "Android runtime" in result.stdout
    assert "ART" in result.stdout


def test_knowledge_cli_show_apk_signing_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "apk_signing"])
    assert result.exit_code == 0
    assert "APK signing and trust" in result.stdout
    assert "v2+" in result.stdout


def test_knowledge_cli_show_android_components_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android_components"])
    assert result.exit_code == 0
    assert "Android component model" in result.stdout
    assert "Activity" in result.stdout
    assert "Intent" in result.stdout


def test_knowledge_cli_apk_anatomy_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "apk-anatomy"])
    assert result.exit_code == 0
    assert "APK Anatomy" in result.stdout
    assert "classes.dex" in result.stdout


def test_knowledge_cli_classify_commands_run() -> None:
    apk_result = CliRunner().invoke(app, ["knowledge", "classify", "--path", "sample.apk"])
    exe_result = CliRunner().invoke(app, ["knowledge", "classify", "--path", "malware.exe"])
    assert apk_result.exit_code == 0
    assert exe_result.exit_code == 0
    assert "Type: Android APK" in apk_result.stdout
    assert "Type: Windows PE" in exe_result.stdout
    assert "Relevant concepts: apk" in apk_result.stdout
    assert "permission_model" in apk_result.stdout


def test_knowledge_cli_classify_rejects_blank_path() -> None:
    result = CliRunner().invoke(app, ["knowledge", "classify", "--path", "   "])
    assert result.exit_code == 1
    assert "artifact path cannot be blank" in result.stdout


def test_knowledge_cli_show_unknown_concept_suggests_close_match() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android-app"])
    assert result.exit_code == 0
    assert "Android app package" in result.stdout
    assert "Did you mean:" not in result.stdout


def test_knowledge_cli_show_unknown_concept_still_rejects_truly_unknown() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "quantum-bean"])
    assert result.exit_code == 1
    assert "Unknown concept" in result.stdout
    assert "Available concepts:" in result.stdout


def test_knowledge_cli_teach_topics() -> None:
    result = CliRunner().invoke(app, ["knowledge", "teach"])
    assert result.exit_code == 0
    assert "Knowledge teaching topics" in result.stdout
    assert "android_fundamentals" in result.stdout
    assert "apk_anatomy" in result.stdout
    assert "learning_pipeline" in result.stdout


def test_knowledge_cli_teach_android_fundamentals() -> None:
    result = CliRunner().invoke(app, ["knowledge", "teach", "android_fundamentals"])
    assert result.exit_code == 0
    assert "android_fundamentals" in result.stdout
    assert "Takeaways:" in result.stdout
    assert "android" in result.stdout.lower()


def test_knowledge_cli_teach_unknown_topic_suggests() -> None:
    result = CliRunner().invoke(app, ["knowledge", "teach", "android stuff"])
    assert result.exit_code == 1
    assert "Unknown lesson" in result.stdout


def test_knowledge_cli_data_topics() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data"])
    assert result.exit_code == 0
    assert "Seed synthetic data topics" in result.stdout
    assert "android_apps" in result.stdout
    assert "permission_levels" in result.stdout
    assert "dataset_rows" in result.stdout
    assert "artifact_types" in result.stdout


def test_knowledge_cli_data_android_apps() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data", "android_apps"])
    assert result.exit_code == 0
    assert "FAKE DATASET: android_apps" in result.stdout
    assert "com.iapetus.seed.bankingwallet" in result.stdout
    assert "target_label: malware" in result.stdout


def test_knowledge_cli_data_permission_levels() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data", "permission_levels"])
    assert result.exit_code == 0
    assert "FAKE DATASET: permission_levels" in result.stdout
    assert "android.permission.CAMERA" in result.stdout
    assert "protection: dangerous" in result.stdout


def test_knowledge_cli_data_dataset_rows() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data", "dataset_rows"])
    assert result.exit_code == 0
    assert "FAKE DATASET: dataset_rows" in result.stdout
    assert "permission_tokens" in result.stdout
    assert "av_tokens" in result.stdout


def test_knowledge_cli_data_artifact_types() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data", "artifact_types"])
    assert result.exit_code == 0
    assert "FAKE DATASET: artifact_types" in result.stdout
    assert ".apk" in result.stdout
    assert "Android APK" in result.stdout
    assert "Android DEX" in result.stdout


def test_knowledge_cli_data_unknown_topic_fails() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data", "quantum"])
    assert result.exit_code == 1
    assert "Unknown synthetic topic" in result.stdout


def test_fake_dataset_row_count_is_stable() -> None:
    assert get_dataset_row_count() == 3


def test_fake_topics_list_matches_public_api() -> None:
    topics = list_fake_topics()
    assert "android_apps" in topics
    assert "permission_levels" in topics
    assert "dataset_rows" in topics
    assert "artifact_types" in topics


def test_knowledge_get_concept_alias_android_app() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "android app"])
    assert result.exit_code == 0
    assert "Android app package" in result.stdout
    assert "declared permissions" in result.stdout


def test_knowledge_cli_show_aab_command_runs() -> None:
    result = CliRunner().invoke(app, ["knowledge", "show", "aab"])
    assert result.exit_code == 0
    assert "Android App Bundle" in result.stdout
    assert "module" in result.stdout


def test_knowledge_cli_data_topics_include_artifact_types() -> None:
    result = CliRunner().invoke(app, ["knowledge", "data"])
    assert result.exit_code == 0
    assert "artifact_types" in result.stdout


def test_artifact_classify_rejects_blank_path_raises_cleanly() -> None:
    result = CliRunner().invoke(app, ["knowledge", "classify", "--path", ""])
    assert result.exit_code == 1
    assert "artifact path cannot be blank" in result.stdout

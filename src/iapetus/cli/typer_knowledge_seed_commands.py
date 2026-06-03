"""Seed knowledge commands."""
from __future__ import annotations

import typer

from iapetus.knowledge import (
    ArtifactClassifier,
    IMPORT_CONTRACT_SPECS,
    KNOWLEDGE_EVAL_FILE_NAME,
    apk_anatomy_lines,
    build_type_training_corpus,
    concept_summary,
    evaluate_android_knowledge,
    fake_data_lines,
    find_matching_concepts,
    find_matching_lessons,
    get_concept,
    lesson_lines,
    list_concept_ids,
    list_fake_topics,
    list_lesson_ids,
    print_concepts,
    preview_training_seed_summary,
    validate_all_import_contract_files,
    write_type_training_corpus,
)

from iapetus.cli.cli_console_and_path_helpers import console

knowledge_app = typer.Typer(help="Knowledge helpers.")


def _run_knowledge_concepts() -> None:
    console.print("[bold]Knowledge concepts[/bold]")
    for concept_line in print_concepts():
        console.print(f"- {concept_line}")


def _run_knowledge_show(concept_id: str) -> None:
    try:
        concept = get_concept(concept_id)
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        suggestions = find_matching_concepts(concept_id)
        if suggestions:
            console.print(f"Did you mean: {', '.join(suggestions)}?")
        console.print(f"Available concepts: {', '.join(list_concept_ids())}")
        raise typer.Exit(code=1)
    console.print(f"[bold]{concept.display_name}[/bold]")
    console.print(concept_summary(concept))
    console.print(f"definition: {concept.definition}")
    console.print(f"key_fields: {', '.join(concept.key_fields) or 'none'}")
    console.print(f"static_evidence: {', '.join(concept.static_evidence) or 'none'}")
    console.print(f"dynamic_evidence: {', '.join(concept.dynamic_evidence) or 'none'}")
    console.print(f"relevant_tools: {', '.join(concept.relevant_tools) or 'none'}")
    console.print(f"iapetus_role: {concept.iapetus_role}")
    console.print(f"notes: {concept.notes}")


def _run_knowledge_apk_anatomy() -> None:
    console.print("[bold]APK Anatomy[/bold]")
    for item in apk_anatomy_lines():
        console.print(f"- {item}")


def _run_knowledge_teach(topic: str | None = None) -> None:
    if topic is None or not topic.strip():
        console.print("[bold]Knowledge teaching topics[/bold]")
        for lesson_id in list_lesson_ids():
            console.print(f"- {lesson_id}")
        console.print("Run with: iapetus knowledge teach <topic>")
        return

    try:
        for line in lesson_lines(topic):
            console.print(line)
        return
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        suggestions = find_matching_lessons(topic)
        if suggestions:
            console.print(f"Did you mean: {', '.join(suggestions)}?")
        console.print(f"Available topics: {', '.join(list_lesson_ids())}")
        raise typer.Exit(code=1)


def _run_knowledge_data(topic: str | None = None) -> None:
    if topic is None or not topic.strip():
        console.print("[bold]Seed synthetic data topics[/bold]")
        for item in list_fake_topics():
            console.print(f"- {item}")
        console.print("Run with: iapetus knowledge data <topic>")
        return

    try:
        for line in fake_data_lines(topic):
            console.print(line)
        return
    except KeyError as exc:
        console.print(f"[red]{exc}[/red]")
        console.print(f"Available topics: {', '.join(list_fake_topics())}")
        raise typer.Exit(code=1)


def _run_knowledge_classify(path: str) -> None:
    try:
        classification = ArtifactClassifier.classify(path)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold]Artifact classification[/bold]")
    console.print(f"Path: {classification.normalized_path}")
    console.print(f"Type: {classification.artifact_type}")
    console.print(f"Evidence: {classification.evidence}")
    if classification.relevant_concepts:
        console.print(
            "Relevant concepts: "
            f"{', '.join(classification.relevant_concepts)}",
        )
    console.print(f"Eligible for Android permission analysis: {classification.relevance.eligible_for_android_permission_analysis}")
    console.print(f"Eligible for Android static analysis: {classification.relevance.eligible_for_android_static_analysis}")
    console.print(f"Eligible for Android dynamic analysis: {classification.relevance.eligible_for_android_dynamic_analysis}")
    console.print(f"Eligible for Windows/PE analysis: {classification.relevance.eligible_for_windows_pe_analysis}")
    console.print(
        "Eligible for future generic AV/vendor-token learning: "
        f"{classification.relevance.eligible_for_generic_av_token_learning}",
    )


def _run_validate_import_contracts() -> None:
    console.print("[bold]Import contract validation[/bold]")
    summaries = validate_all_import_contract_files()
    for summary in summaries:
        console.print(f"File           : {summary.file_name}")
        console.print(f"Row count      : {summary.row_count}")
        console.print(f"Valid count    : {summary.valid_count}")
        console.print(f"Invalid count  : {summary.invalid_count}")
        console.print(f"Record types   : {', '.join(summary.record_types_found) or 'none'}")
        console.print(f"Training count : {summary.training_eligible_count}")
        console.print(f"Training cand. : {summary.training_candidate_count}")
        console.print(f"Training appr. : {summary.training_approved_count}")
        console.print(f"Teaching only  : {summary.teaching_only_count}")
        console.print(f"Explanation only: {summary.explanation_only_count}")
        console.print(f"Validation only: {summary.validation_only_count}")
        if summary.synthetic_heavy:
            console.print("[yellow]Warning       : synthetic-heavy data[/yellow]")
        for issue in summary.issues:
            console.print(f"[red]Issue         : row {issue.row_number} - {issue.message}[/red]")
        console.print("")


def _run_preview_training_seeds() -> None:
    summary = preview_training_seed_summary()
    console.print("[bold]Training Seed Preview[/bold]")
    console.print(f"Permission facts          : {summary['permission_fact_count']}")
    console.print(f"Trainable permission facts: {summary['training_candidate_permission_facts']}")
    console.print(f"Malware patterns          : {summary['malware_type_pattern_count']}")
    console.print(f"Trainable malware patterns: {summary['trainable_malware_type_patterns']}")
    console.print(f"Benign archetypes         : {summary['benign_archetype_count']}")
    console.print(f"Trainable benign archetypes: {summary['trainable_benign_archetypes']}")
    console.print(f"Contrast examples         : {summary['contrast_example_count']}")
    console.print(f"Contrast teaching-only    : {summary['contrast_teaching_only_count']}")
    console.print(f"Contrast explanation-only : {summary['contrast_explanation_only_count']}")


def _run_build_type_corpus(write: bool = False) -> None:
    corpus = build_type_training_corpus()
    console.print("[bold]Type Training Corpus[/bold]")
    console.print(f"Corpus name   : {corpus['corpus_name']}")
    console.print(f"Examples      : {corpus['example_count']}")
    console.print(f"Authority facts: {corpus['authority_fact_count']}")
    console.print(f"Contrast rows : {corpus['contrast_example_count']}")
    for label, count in sorted(corpus["class_counts"].items()):
        console.print(f"  - {label}: {count}")
    for warning in corpus["warnings"]:
        console.print(f"[yellow]Warning: {warning}[/yellow]")
    if write:
        path = write_type_training_corpus()
        console.print(f"[green]Wrote type corpus: {path}[/green]")


def _run_knowledge_eval() -> None:
    summary = evaluate_android_knowledge()
    console.print("[bold]Android Knowledge Eval[/bold]")
    console.print(f"Benchmark file : {KNOWLEDGE_EVAL_FILE_NAME}")
    console.print(f"Total questions: {summary.total_questions}")
    console.print(f"Covered        : {summary.covered_count}")
    console.print(f"Partial        : {summary.partial_count}")
    console.print(f"Gaps           : {summary.gap_count}")
    console.print("Gaps by topic  :")
    if summary.gaps_by_topic:
        for topic, count in summary.gaps_by_topic.items():
            console.print(f"  - {topic}: {count}")
    else:
        console.print("  - none")
    console.print("Gaps by difficulty:")
    if summary.gaps_by_difficulty:
        for difficulty, count in summary.gaps_by_difficulty.items():
            console.print(f"  - {difficulty}: {count}")
    else:
        console.print("  - none")
    console.print("Trick questions not fully covered:")
    if summary.trick_questions_not_fully_covered:
        for result in summary.trick_questions_not_fully_covered:
            console.print(f"  - {result.question_id} ({result.status})")
    else:
        console.print("  - none")
    console.print("Recommended next seed topics:")
    if summary.recommended_next_seed_topics:
        for topic in summary.recommended_next_seed_topics:
            console.print(f"  - {topic}")
    else:
        console.print("  - none")


@knowledge_app.command("concepts")
def knowledge_concepts() -> None:
    """List built-in knowledge concept IDs."""
    _run_knowledge_concepts()


@knowledge_app.command("show")
def knowledge_show(concept: str) -> None:
    """Show a built-in knowledge concept."""
    _run_knowledge_show(concept.strip())


@knowledge_app.command("apk-anatomy")
def knowledge_apk_anatomy() -> None:
    """Show the APK anatomy reference list."""
    _run_knowledge_apk_anatomy()


@knowledge_app.command("classify")
def knowledge_classify(path: str = typer.Option(..., "--path", help="Path to classify")) -> None:
    """Classify a file into a conservative artifact type."""
    _run_knowledge_classify(path=path)


@knowledge_app.command("teach")
def knowledge_teach(topic: str | None = typer.Argument(None, help="Optional lesson topic to print")) -> None:
    """Print a seed learning lesson for Android/AI operator context."""
    _run_knowledge_teach(topic=topic)


@knowledge_app.command("data")
def knowledge_data(topic: str | None = typer.Argument(None, help="Optional synthetic data topic")) -> None:
    """Show seed synthetic Android data used for learning."""
    _run_knowledge_data(topic=topic)


@knowledge_app.command("validate-import-contracts")
def knowledge_validate_import_contracts() -> None:
    """Validate Windows-native Android security import contract JSONL files."""
    _run_validate_import_contracts()


@knowledge_app.command("preview-training-seeds")
def knowledge_preview_training_seeds() -> None:
    """Preview governed teaching/training seed counts for type-oriented learning."""
    _run_preview_training_seeds()


@knowledge_app.command("build-type-corpus")
def knowledge_build_type_corpus(
    write: bool = typer.Option(False, "--write", help="Write data/generated/type_training_corpus.json."),
) -> None:
    """Build a first type-oriented corpus from governed Android security import contracts."""
    _run_build_type_corpus(write=write)


@knowledge_app.command("eval")
def knowledge_eval() -> None:
    """Evaluate how well the current Android teaching corpus covers benchmark questions."""
    _run_knowledge_eval()

"""Seed knowledge commands."""
from __future__ import annotations

import typer

from iapetus.knowledge import (
    ArtifactClassifier,
    apk_anatomy_lines,
    concept_summary,
    fake_data_lines,
    find_matching_concepts,
    find_matching_lessons,
    get_concept,
    lesson_lines,
    list_concept_ids,
    list_fake_topics,
    list_lesson_ids,
    print_concepts,
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

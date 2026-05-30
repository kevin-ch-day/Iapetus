from __future__ import annotations

from iapetus.labels import (
    MalwareLabel,
    NormalAppLabel,
    render_malware_label,
    render_normal_app_label,
)
from iapetus.labels.renderer import InvalidLabelError


def test_render_malware_label() -> None:
    value = render_malware_label(
        MalwareLabel(
            platform="AndroidOS",
            malware_primary="Trojan",
            family="Anubis",
            variant="t",
            subtype="Banker",
        )
    )
    assert value == "AndroidOS:Trojan.Anubis-t:[Banker]"


def test_render_normal_app_label() -> None:
    value = render_normal_app_label(
        NormalAppLabel(
            platform="AndroidOS",
            app_name="Facebook",
            build_ref="64543615",
            app_category="SocialMedia",
        )
    )
    assert value == "AndroidOS:Facebook-64543615:[SocialMedia]"


def test_invalid_label_part_fails() -> None:
    try:
        render_malware_label(
            MalwareLabel(
                platform="AndroidOS",
                malware_primary="Trojan",
                family="Anubis",
                variant="t",
                subtype="Banker:bad",
            )
        )
    except InvalidLabelError:
        return
    assert False, "Expected InvalidLabelError"

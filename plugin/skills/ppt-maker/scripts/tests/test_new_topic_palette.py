"""
new_topic.py --palette 색 배정 회귀 테스트 (표준 unittest, 외부 의존 없음).

실행:
    python -m unittest discover -s plugin/skills/ppt-maker/scripts/tests -v

지키는 것(결정 #24 보강):
    1) 내장 팔레트 전부 — 본문 7:1 · 보조 글자 4.5:1 · 강조 3:1 명암비를 넘는다
    2) 강조색이 본문 글자색과 구분된다(1.8:1 이상)
    3) 어두운 팔레트(dark-premium)는 어두운 바탕이 된다
    4) 첫 줄을 조정 2개 이하로 쓸 수 있으면 첫 줄을 쓴다(팔레트 대표 색 유지)
    5) 새 topic 생성 전체 흐름이 임시 폴더에서 끝까지 돈다
    6) 보조 강조색(secondary)이 있고 바탕 대비 3:1을 넘으며 강조색과 다르다(P7 iteration-2: 단조로운 색)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import new_topic as nt  # noqa: E402


def roles_of(design_text: str) -> dict[str, str]:
    """DESIGN.md front matter의 colors 값을 읽는다."""
    return dict(re.findall(r'  ([a-z-]+): "(#[0-9A-F]{6})"', design_text))


class PaletteRoleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.names = sorted(p.stem for p in nt.PALETTES_DIR.glob("*.md"))
        self.assertTrue(self.names, "내장 팔레트가 없다")

    def test_contrast_all_palettes(self) -> None:
        for name in self.names:
            with self.subTest(palette=name):
                r = roles_of(nt.design_from_palette(name))
                self.assertGreaterEqual(nt.contrast(r["ink"], r["canvas"]), nt.INK_MIN)
                self.assertGreaterEqual(nt.contrast(r["ink-muted"], r["canvas"]), nt.MUTED_MIN)
                self.assertGreaterEqual(nt.contrast(r["primary"], r["canvas"]), nt.PRIMARY_MIN)
                self.assertGreaterEqual(nt.contrast(r["ink-muted"], r["surface"]), nt.MUTED_MIN)

    def test_primary_apart_from_ink(self) -> None:
        for name in self.names:
            with self.subTest(palette=name):
                r = roles_of(nt.design_from_palette(name))
                self.assertGreaterEqual(nt.contrast(r["primary"], r["ink"]), nt.PRIMARY_APART)

    def test_secondary_accent(self) -> None:
        for name in self.names:
            with self.subTest(palette=name):
                r = roles_of(nt.design_from_palette(name))
                self.assertIn("secondary", r)
                self.assertGreaterEqual(nt.contrast(r["secondary"], r["canvas"]), nt.PRIMARY_MIN)
                self.assertNotEqual(r["secondary"], r["primary"])

    def test_dark_palette_has_dark_canvas(self) -> None:
        for name in nt.DARK_PALETTES:
            r = roles_of(nt.design_from_palette(name))
            self.assertLess(nt.luminance(r["canvas"]), nt.luminance(r["ink"]))

    def test_first_row_kept_when_few_adjustments(self) -> None:
        # neon-electric 첫 줄은 바탕 조정 1개로 쓸 수 있다 → 조정 없는 다른 줄로 넘어가지 않아야 한다
        text = nt.design_from_palette("neon-electric")
        self.assertIn("1번째 줄", text)

    def test_mix_and_move_until(self) -> None:
        self.assertEqual(nt.mix("#000000", "#FFFFFF", 0), "#000000")
        self.assertEqual(nt.mix("#000000", "#FFFFFF", 1), "#FFFFFF")
        self.assertEqual(nt.move_until("#777777", "#FFFFFF", lambda _c: False), "#FFFFFF")


class NewTopicCliTest(unittest.TestCase):
    def test_palette_topic_in_temp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = subprocess.run(
                [sys.executable, str(SCRIPTS / "new_topic.py"), "--slug", "palette-test", "--title", "팔레트 시험",
                 "--type", "general", "--palette", "bold-energetic", "--root", tmp],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            design = (Path(tmp) / "topics" / "palette-test" / "DESIGN.md").read_text(encoding="utf-8")
            self.assertIn("명도 조정:", design)
            self.assertEqual(len(roles_of(design)), 7)  # primary·secondary·canvas·surface·ink·ink-muted·hairline


if __name__ == "__main__":
    unittest.main()

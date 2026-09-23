"""
serve_live.py 회귀 테스트 (표준 unittest, 외부 의존 없음).

실행:
    python -m unittest discover -s plugin/skills/ppt-maker/scripts/tests -v

테스트 덱은 이 파일 안에서 만든다. 플러그인으로 배포하면 topics/가 함께 가지 않으므로
저장소의 topics/_sample에 기대지 않는다.

지키는 것(50th 버그 4개의 재발 방지):
    1) 블록 경계 — 2번 장면을 고치면 같은 문구의 3번 장면은 그대로
    2) 같은 문구 반복 — NTH 없으면 ambiguous 거부, NTH 있으면 그 자리만
    3) 상태 코드 — 전부 200 / 일부 409 / 0건 422 / 다른 topic 400
    4) 단일 저장 대상 + .bak 1개
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve_live as sl  # noqa: E402

FIXTURE = """<!doctype html><html><head><style id="scene-styles">.scene{}</style></head><body>
<div class="detail-frame" id="detail-frame">
<!-- SLIDES START -->
<section class="scene" data-slide="1" data-skill="title">
  <h1 class="hero-title" data-editable="true">첫 장면</h1>
</section>

<section class="scene" data-slide="2" data-skill="title-bullets">
  <h2 class="scene-title" data-editable="true">둘째 장면</h2>
  <div class="stack">
    <div class="stack"><span class="chip" data-editable="true">같은 칩</span></div>
    <span class="chip" data-editable="true">같은 칩</span>
  </div>
  <div class="deck-footer" data-editable="true">공통 꼬리말</div>
</section>

<section class="scene" data-slide="3" data-skill="stat">
  <h2 class="scene-title" data-editable="true">셋째 장면</h2>
  <div class="deck-footer" data-editable="true">공통 꼬리말</div>
</section>

<section class="scene" data-slide="10" data-skill="quote">
  <p class="quote-body" data-editable="true">열째 장면 &amp; 인용</p>
</section>
<!-- SLIDES END -->
</div></body></html>
"""


def patch(*entries: tuple) -> str:
    """(장면, 셀렉터, OLD, NEW[, NTH]) 묶음으로 브라우저와 같은 형식의 패치를 만든다."""
    out = "# Overview edits — test\n\n"
    for e in entries:
        slide, sel, old, new = e[:4]
        nth = e[4] if len(e) > 4 else 0
        out += f"## Slide {slide}\n- {sel}\n"
        if nth:
            out += f"  NTH: {nth}\n"
        out += f"  OLD: {old}\n  NEW: {new}\n\n"
    return out


def block_text(html: str, n: int) -> str:
    s, e = sl.find_block(html, n)
    assert s is not None
    return html[s:e]


class ParsePatchTest(unittest.TestCase):
    def test_nth_and_fields(self) -> None:
        changes = sl.parse_patch(patch((2, ".chip", "같은 칩", "새 칩", 2), (3, ".deck-footer", "a", "b")))
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0], {"slide": "2", "selector": ".chip", "nth": 2, "old": "같은 칩", "new": "새 칩"})
        self.assertEqual(changes[1]["nth"], 0)

    def test_multiline_new(self) -> None:
        text = "## Slide 1\n- .hero-title\n  OLD: 첫 장면\n  NEW: 첫째 줄\n둘째 줄\n"
        self.assertEqual(sl.parse_patch(text)[0]["new"], "첫째 줄\n둘째 줄")


class FindBlockTest(unittest.TestCase):
    def test_section_boundary(self) -> None:
        b2 = block_text(FIXTURE, 2)
        self.assertTrue(b2.startswith('<section class="scene" data-slide="2"'))
        self.assertTrue(b2.endswith("</section>"))
        self.assertNotIn("셋째 장면", b2)

    def test_slide_1_is_not_slide_10(self) -> None:
        self.assertIn("첫 장면", block_text(FIXTURE, 1))
        self.assertIn("열째 장면", block_text(FIXTURE, 10))
        self.assertNotIn("열째 장면", block_text(FIXTURE, 1))

    def test_missing_slide(self) -> None:
        self.assertEqual(sl.find_block(FIXTURE, 99), (None, None))


class ApplyChangesTest(unittest.TestCase):
    def test_footer_edit_touches_only_its_slide(self) -> None:
        html, applied, failed = sl.apply_changes(FIXTURE, sl.parse_patch(patch((2, ".deck-footer", "공통 꼬리말", "둘째 꼬리말"))))
        self.assertEqual((applied, failed), (1, []))
        self.assertIn("둘째 꼬리말", block_text(html, 2))
        self.assertIn("공통 꼬리말", block_text(html, 3))
        self.assertEqual(html.count("공통 꼬리말"), 1)

    def test_repeated_text_without_nth_is_ambiguous(self) -> None:
        html, applied, failed = sl.apply_changes(FIXTURE, sl.parse_patch(patch((2, ".chip", "같은 칩", "바뀐 칩"))))
        self.assertEqual(applied, 0)
        self.assertIn("ambiguous", failed[0]["reason"])
        self.assertEqual(html, FIXTURE)

    def test_repeated_text_with_nth(self) -> None:
        html, applied, _ = sl.apply_changes(FIXTURE, sl.parse_patch(patch((2, ".chip", "같은 칩", "바뀐 칩", 2))))
        self.assertEqual(applied, 1)
        b2 = block_text(html, 2)
        self.assertLess(b2.index("같은 칩"), b2.index("바뀐 칩"))   # 첫째는 그대로, 둘째만 바뀜

    def test_nested_same_class_keeps_structure(self) -> None:
        # 바깥 .stack은 안쪽 HTML이 old와 다르므로 후보가 아니다 → 구조가 깨지지 않는다
        html, applied, _ = sl.apply_changes(FIXTURE, sl.parse_patch(patch((2, ".chip", "같은 칩", "X", 1))))
        self.assertEqual(applied, 1)
        self.assertEqual(html.count("<section"), FIXTURE.count("<section"))
        self.assertEqual(html.count("</div>"), FIXTURE.count("</div>"))

    def test_entity_normalization(self) -> None:
        # 브라우저 innerHTML은 &amp;를 그대로 주고, 파일에도 &amp;가 있다 → 같은 것으로 본다
        _, applied, _ = sl.apply_changes(FIXTURE, sl.parse_patch(patch((10, ".quote-body", "열째 장면 &amp; 인용", "새 인용"))))
        self.assertEqual(applied, 1)

    def test_wrong_old(self) -> None:
        _, applied, failed = sl.apply_changes(FIXTURE, sl.parse_patch(patch((3, ".scene-title", "없는 문구", "x"))))
        self.assertEqual(applied, 0)
        self.assertEqual(failed[0]["reason"], "OLD 문구를 찾지 못함")


class HttpTest(unittest.TestCase):
    """임시 프로젝트(root/topics/t/overview.html)로 실제 서버를 띄워 상태 코드를 확인한다."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.topic = Path(self.tmp.name) / "topics" / "t"
        self.topic.mkdir(parents=True)
        self.overview = self.topic / "overview.html"
        self.overview.write_text(FIXTURE, encoding="utf-8", newline="")
        self.server = sl.make_server(self.topic, port=0)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def save(self, text: str, page: str | None = "/topics/t/overview.html") -> tuple[int, dict]:
        body = {"patch": text}
        if page is not None:
            body["page"] = page
        return self.request("/save", body)

    def test_all_applied_200_and_bak(self) -> None:
        code, res = self.save(patch((2, ".deck-footer", "공통 꼬리말", "둘째 꼬리말")))
        self.assertEqual((code, res["applied"], res["changes_requested"]), (200, 1, 1))
        self.assertIn("둘째 꼬리말", self.overview.read_text(encoding="utf-8"))
        self.assertEqual((self.topic / "overview.html.bak").read_text(encoding="utf-8"), FIXTURE)

    def test_partial_409(self) -> None:
        code, res = self.save(patch((2, ".deck-footer", "공통 꼬리말", "둘째 꼬리말"), (3, ".scene-title", "없는 문구", "x")))
        self.assertEqual((code, res["applied"], res["changes_requested"]), (409, 1, 2))
        self.assertEqual(res["failed"][0]["slide"], "3")

    def test_none_422_and_file_untouched(self) -> None:
        code, res = self.save(patch((3, ".scene-title", "없는 문구", "x")))
        self.assertEqual((code, res["applied"]), (422, 0))
        self.assertEqual(self.overview.read_text(encoding="utf-8"), FIXTURE)
        self.assertFalse((self.topic / "overview.html.bak").exists())

    def test_other_topic_page_400(self) -> None:
        code, _ = self.save(patch((2, ".deck-footer", "공통 꼬리말", "x")), page="/topics/other/overview.html")
        self.assertEqual(code, 400)
        self.assertEqual(self.overview.read_text(encoding="utf-8"), FIXTURE)

    def test_mtime(self) -> None:
        code, res = self.request("/mtime?page=/topics/t/overview.html")
        self.assertEqual(code, 200)
        self.assertTrue(res["mtime"].isdigit())
        code, _ = self.request("/mtime?page=/topics/other/overview.html")
        self.assertEqual(code, 404)

    def test_static_serving_from_project_root(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/topics/t/overview.html", timeout=5) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("SLIDES START", r.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

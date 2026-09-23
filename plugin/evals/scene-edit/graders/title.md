---
type: regex
target: { source: file, path: topics/_sample/overview.html }
pattern: '<section(?=[^>]*data-slide="2")[^>]*>(?:(?!</section>)[\s\S])*?<h2[^>]*\bscene-title\b[^>]*>\s*세 가지 확인 방법\s*</h2>'
---

2번 장면 제목이 정확히 '세 가지 확인 방법'이다

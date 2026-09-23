---
type: regex
target: { source: file, path: topics/_sample/overview.html }
pattern: '<section(?=[^>]*data-slide="2")(?=[^>]*data-scene-id="S02")[^>]*>(?:(?!</section>)[\s\S])*?<aside class="speaker-note">\s*세\s+가지를\s+차례로\s+확인합니다\.\s+편집,\s+발표,\s+PDF입니다\.\s*</aside>'
---

2번 장면의 data-scene-id S02와 speaker-note 원문이 유지된다

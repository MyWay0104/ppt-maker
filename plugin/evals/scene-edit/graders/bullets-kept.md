---
type: regex
target: { source: file, path: topics/_sample/overview.html }
pattern: '<section(?=[^>]*data-slide="2")[^>]*>(?=(?:(?!</section>)[\s\S])*?overview\.html에서\s+Aim과\s+Edit로\s+고친다)(?=(?:(?!</section>)[\s\S])*?present\.html로\s+발표하고\s+발표자\s+창을\s+띄운다)(?=(?:(?!</section>)[\s\S])*?PDF는\s+장면\s+수와\s+같은\s+쪽수로\s+나온다)'
---

원래 2번 장면의 불릿 문구 3개가 2번 장면에 그대로 남아 있다

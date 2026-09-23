---
type: regex
target: { source: file, path: topics/_sample/overview.html }
pattern: '<section(?=[^>]*data-slide="2")[^>]*>(?:(?!</section>)[\s\S])*?class="[^"]*\bcompare-grid\b(?:(?!</section>)[\s\S])*?\bcompare-col\b(?:(?!</section>)[\s\S])*?\bcompare-heading\b(?:(?!</section>)[\s\S])*?<ul[^>]*\bcompare-list\b(?:(?!</section>)[\s\S])*?\bcompare-col\b(?:(?!</section>)[\s\S])*?\bcompare-heading\b(?:(?!</section>)[\s\S])*?<ul[^>]*\bcompare-list\b'
---

2번 장면이 compare 마크업(.compare-grid 안에 .compare-col 2개 이상, 각 칸에 .compare-heading과 ul.compare-list)이다

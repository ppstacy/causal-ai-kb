---
layout: default
title: Daily picks
permalink: /daily/
---

# Daily picks

Each weekday morning a new top-5 picks list is auto-generated from the
day's fetched items. RSS feed: [feed.xml]({{ '/daily/feed.xml' | relative_url }}).

{% assign days = site.pages | where_exp: "p", "p.path contains '/daily/'" | where_exp: "p", "p.path contains '/picks.md'" | sort: 'path' | reverse %}
{% if days.size == 0 %}
_No picks yet — the first run will land here._
{% else %}
{% for d in days %}
- **[{{ d.date | default: d.title }}]({{ d.url | relative_url }})**{% if d.title and d.title != d.date %} — {{ d.title }}{% endif %}
{% endfor %}
{% endif %}

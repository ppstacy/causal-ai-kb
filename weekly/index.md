---
layout: default
title: Weekly archive
permalink: /weekly/
---

# Weekly archive

Every Friday afternoon a new digest is published rolling up the past
week's items. RSS feed: [feed.xml]({{ '/weekly/feed.xml' | relative_url }}).

{% assign weeklies = site.pages | where_exp: "p", "p.path contains 'weekly/'" | where_exp: "p", "p.name contains '-W'" | sort: "name" | reverse %}
{% if weeklies.size == 0 %}
_No issues yet. The first digest will appear here after the next Friday
publication._
{% else %}
{% for w in weeklies %}
- **[{{ w.name | replace: '.md', '' }}]({{ w.url | relative_url }})**{% if w.title and w.title != w.name %} — {{ w.title }}{% endif %}
{% endfor %}
{% endif %}

---
pagetitle: {{ page_title }}
date: February 19, 2020
prev_url: {{ url_for("render_fixed_day", month=date|get_date('yesterday','m'), day=date|get_date('yesterday','d')) }}
prev_date: {{ date|get_date('yesterday','-b') }} {{ date|get_date('yesterday','-d') }}
this_url: {{ url_for("render_fixed_day", month=date|get_date('today','m'), day=date|get_date('today','d')) }}
this_date: {{ date|get_date('today','-b') }} {{ date|get_date('today','-d') }}
next_url: {{ url_for("render_fixed_day", month=date|get_date('tomorrow','m'), day=date|get_date('tomorrow','d')) }}
next_date: {{ date|get_date('tomorrow','-b') }} {{ date|get_date('tomorrow','-d') }}
---
{% for c in content %}
{% include c['type'] + '_t.md' %}
{% for k, v in c.prooftexts.items() %}
[fn:{{ c.abbv }}{{ k }}]: {{ v | safe | replace("\n", " ")}}
{% endfor %}
{% endfor %}

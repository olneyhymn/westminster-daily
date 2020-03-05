#### {{ c['name'] }}

{{ c['number'] }}. {{ c['question'] | safe}}

A. {{ c['answer'] | safe | regex_replace("<sup id='(.*?)'>.*?</sup>", "[^\\1]") }}


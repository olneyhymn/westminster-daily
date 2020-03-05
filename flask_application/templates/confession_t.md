#### {{ c['name'] }}

##### {{ c['title'] }}

{{ c['paragraph'] }}. {{ c['body'] | safe | regex_replace("<sup id='(.*?)'>.*?</sup>", "[^\\1]") }}

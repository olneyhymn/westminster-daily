"""
Generate weekly markdown content files for Heidelberg Weekly
Creates content-heidelberg/week-NN/index.md for all 52 weeks
"""

import json
import yaml
import os
from datetime import datetime, timedelta
import calendar

# Load the plan
with open('heidelberg_application/plan.yaml', 'r') as f:
    plan = yaml.safe_load(f)

# Load the Heidelberg data
with open('static/confessions/heidelberg.json', 'r') as f:
    heidelberg = json.load(f)

# Month names for navigation
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def get_week_date_range(week_num):
    """
    Calculate the date range for a given week (1-52).
    Week 1 starts on the first Sunday of January.
    """
    # Find first Sunday of January 2024
    year = 2024
    jan_1 = datetime(year, 1, 1)
    days_until_sunday = (6 - jan_1.weekday()) % 7  # Sunday is 6 in Python's weekday()
    if days_until_sunday == 0 and jan_1.weekday() == 6:
        # January 1 is already a Sunday
        first_sunday = jan_1
    else:
        first_sunday = jan_1 + timedelta(days=days_until_sunday)
        if first_sunday.day > 7:  # If it's the second week, use the actual first Sunday
            first_sunday = jan_1 + timedelta(days=(6 - jan_1.weekday()))

    # Calculate the Sunday for this week (week_num is 1-based)
    sunday = first_sunday + timedelta(weeks=week_num - 1)

    return sunday

def format_prooftexts_markdown(q_data):
    """Format prooftexts as markdown footnotes"""
    answer = q_data['answer']
    prooftexts = q_data.get('prooftexts', {})
    prooftext_verses = q_data.get('prooftext_verses', {})

    # Clean up answer - remove "Answer:" prefix if present
    answer = answer.replace('Answer:', '').strip()

    # Build footnote references in answer
    footnote_refs = []
    for marker in sorted(prooftexts.keys()):
        # Create unique footnote ID
        footnote_id = f"fn{marker}"
        footnote_refs.append((marker, footnote_id))

    # Build the footnotes section
    footnotes = []
    for marker, footnote_id in footnote_refs:
        if marker in prooftext_verses:
            verses_text = prooftext_verses[marker]
            # Format as markdown footnote
            footnotes.append(f"[^{footnote_id}]: {verses_text}")

    return answer, '\n\n'.join(footnotes)

def generate_weekly_content(week_index):
    """Generate markdown content for a specific week (0-51)"""
    week_data = plan[week_index]
    lords_day = week_data['lords_day']
    title = week_data['title']
    questions = week_data['questions']
    group = week_data['group']

    # Calculate week number (1-52)
    week_num = week_index + 1

    # Get date info
    sunday = get_week_date_range(week_num)
    week_str = f"{month_names[sunday.month-1]} {sunday.day}"

    # Navigation
    prev_week = (week_index - 1) % 52
    next_week = (week_index + 1) % 52

    prev_num = prev_week + 1
    next_num = next_week + 1

    prev_date = get_week_date_range(prev_num)
    next_date = get_week_date_range(next_num)

    prev_week_str = f"{month_names[prev_date.month-1]} {prev_date.day}"
    next_week_str = f"{month_names[next_date.month-1]} {next_date.day}"

    # Format week number with leading zero
    week_fmt = f"{week_num:02d}"
    prev_fmt = f"{prev_num:02d}"
    next_fmt = f"{next_num:02d}"

    # Build the markdown content
    frontmatter = f"""---
pagetitle: "Lord's Day {lords_day}: {title}"
prev_url: /heidelberg-weekly/week-{prev_fmt}/
prev_week: "Week {prev_num}"
this_url: /heidelberg-weekly/week-{week_fmt}/
week_number: "{week_fmt}"
this_week: "Week {week_num}"
lords_day: "{lords_day}"
next_url: /heidelberg-weekly/week-{next_fmt}/
next_week: "Week {next_num}"
---

"""

    # Build content
    content_lines = [frontmatter]
    content_lines.append(f"## Lord's Day {lords_day}\n")
    content_lines.append(f"### {title}\n")
    content_lines.append(f"*{group}*\n")

    all_footnotes = []

    # Add each question and answer
    for q_num in questions:
        q_data = heidelberg.get(str(q_num))
        if not q_data:
            continue

        question = q_data['question']
        # Remove "Question N:" prefix
        question = question.replace(f'Question {q_num}:', '').strip()

        content_lines.append(f"#### Question {q_num}\n")
        content_lines.append(f"{question}\n")
        content_lines.append(f"##### Answer\n")

        # Format answer with prooftexts
        answer, footnotes = format_prooftexts_markdown(q_data)

        # Add footnote markers to answer
        prooftexts = q_data.get('prooftexts', {})
        for marker in sorted(prooftexts.keys()):
            footnote_id = f"fn{marker}"
            # Replace (a), (b), (c) markers with footnote references
            answer = answer.replace(f'({marker})', f'[^{footnote_id}]')

        content_lines.append(f"{answer}\n")

        if footnotes:
            all_footnotes.append(footnotes)

    # Add all footnotes at the end
    if all_footnotes:
        content_lines.append("\n---\n")
        content_lines.append("### Scripture References\n")
        content_lines.append('\n\n'.join(all_footnotes))

    return '\n'.join(content_lines)

# Create output directory
os.makedirs('content-heidelberg', exist_ok=True)

# Generate all 52 weeks
for week_index in range(52):
    week_num = week_index + 1
    week_fmt = f"{week_num:02d}"

    # Create week directory
    week_dir = f'content-heidelberg/week-{week_fmt}'
    os.makedirs(week_dir, exist_ok=True)

    # Generate content
    content = generate_weekly_content(week_index)

    # Write markdown file
    with open(f'{week_dir}/index.md', 'w') as f:
        f.write(content)

    lords_day = plan[week_index]['lords_day']
    title = plan[week_index]['title']
    print(f"Generated Week {week_num:2d} (Lord's Day {lords_day:2d}): {title}")

print(f"\nGenerated {52} weekly content files in content-heidelberg/")

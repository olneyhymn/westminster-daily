"""
Generate heidelberg_application/plan.yaml from the parsed data
"""

import json
import yaml

# Traditional titles for each Lord's Day
lords_day_titles = {
    1: "Our Only Comfort",
    2: "The Knowledge of Our Misery",
    3: "Original Sin",
    4: "God's Justice and Mercy",
    5: "The Only Way of Deliverance",
    6: "The Mediator",
    7: "Saving Faith",
    8: "The Trinity",
    9: "God the Father and Our Creation",
    10: "God's Providence",
    11: "The Name of Jesus",
    12: "The Name of Christ",
    13: "The Name of Christian and the Son of God",
    14: "The Conception and Birth of Christ",
    15: "The Sufferings of Christ",
    16: "Christ's Death and Burial",
    17: "The Resurrection of Christ",
    18: "The Ascension of Christ",
    19: "Christ at the Right Hand of God",
    20: "The Holy Spirit",
    21: "The Holy Catholic Church",
    22: "The Resurrection of the Body and Life Everlasting",
    23: "Our Righteousness Before God",
    24: "Good Works",
    25: "The Sacraments",
    26: "Holy Baptism (1)",
    27: "Holy Baptism (2)",
    28: "The Lord's Supper (1)",
    29: "The Lord's Supper (2)",
    30: "The Lord's Supper (3)",
    31: "The Keys of the Kingdom",
    32: "Good Works and Conversion",
    33: "True Conversion",
    34: "The Law of God and the First Commandment",
    35: "The Second Commandment",
    36: "The Third Commandment (1)",
    37: "The Third Commandment (2)",
    38: "The Fourth Commandment",
    39: "The Fifth Commandment",
    40: "The Sixth Commandment",
    41: "The Seventh Commandment",
    42: "The Eighth Commandment",
    43: "The Ninth Commandment",
    44: "The Tenth Commandment",
    45: "Prayer and the Lord's Prayer",
    46: "The Address of the Lord's Prayer",
    47: "The First Petition",
    48: "The Second Petition",
    49: "The Third Petition",
    50: "The Fourth Petition",
    51: "The Fifth Petition",
    52: "The Sixth Petition and the Conclusion"
}

# Three-part division
part_mapping = {
    1: "Introduction",
    2: "Human Misery", 3: "Human Misery", 4: "Human Misery",
    5: "Divine Deliverance", 6: "Divine Deliverance", 7: "Divine Deliverance",
    8: "Divine Deliverance", 9: "Divine Deliverance", 10: "Divine Deliverance",
    11: "Divine Deliverance", 12: "Divine Deliverance", 13: "Divine Deliverance",
    14: "Divine Deliverance", 15: "Divine Deliverance", 16: "Divine Deliverance",
    17: "Divine Deliverance", 18: "Divine Deliverance", 19: "Divine Deliverance",
    20: "Divine Deliverance", 21: "Divine Deliverance", 22: "Divine Deliverance",
    23: "Divine Deliverance", 24: "Divine Deliverance", 25: "Divine Deliverance",
    26: "Divine Deliverance", 27: "Divine Deliverance", 28: "Divine Deliverance",
    29: "Divine Deliverance", 30: "Divine Deliverance", 31: "Divine Deliverance",
    32: "Christian Gratitude", 33: "Christian Gratitude", 34: "Christian Gratitude",
    35: "Christian Gratitude", 36: "Christian Gratitude", 37: "Christian Gratitude",
    38: "Christian Gratitude", 39: "Christian Gratitude", 40: "Christian Gratitude",
    41: "Christian Gratitude", 42: "Christian Gratitude", 43: "Christian Gratitude",
    44: "Christian Gratitude", 45: "Christian Gratitude", 46: "Christian Gratitude",
    47: "Christian Gratitude", 48: "Christian Gratitude", 49: "Christian Gratitude",
    50: "Christian Gratitude", 51: "Christian Gratitude", 52: "Christian Gratitude"
}

# Load the mapping
with open('/home/user/westminster-daily/lords_day_mapping.json', 'r') as f:
    lords_day_mapping = json.load(f)

# Create the plan
plan = {}

for ld_num in range(1, 53):  # 1-52
    ld_str = str(ld_num)
    questions = lords_day_mapping.get(ld_str, [])

    # Plan uses 0-based index (0-51) but Lord's Day is 1-based (1-52)
    plan_index = ld_num - 1

    plan[plan_index] = {
        'lords_day': ld_num,
        'title': lords_day_titles.get(ld_num, f"Lord's Day {ld_num}"),
        'group': part_mapping.get(ld_num, "Unknown"),
        'questions': questions
    }

# Save as YAML
with open('/home/user/westminster-daily/heidelberg_application/plan.yaml', 'w') as f:
    yaml.dump(plan, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

print(f"Created plan.yaml with {len(plan)} weeks")

# Print summary
print("\n=== Plan Summary ===")
for i in range(min(5, len(plan))):  # First 5
    entry = plan[i]
    print(f"Week {i} (LD {entry['lords_day']}): {entry['title']} - Q{min(entry['questions'])}-{max(entry['questions'])}")

print("...")

for i in range(max(0, len(plan)-3), len(plan)):  # Last 3
    entry = plan[i]
    print(f"Week {i} (LD {entry['lords_day']}): {entry['title']} - Q{min(entry['questions'])}-{max(entry['questions'])}")

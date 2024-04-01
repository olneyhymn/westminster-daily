#!/usr/bin/env python3

import json
from contextlib import redirect_stdout
import io
from elevenlabs import save
from elevenlabs.client import ElevenLabs
import inflect
import os

import re

# as per recommendation from @freylis, compile once only
CLEANR = re.compile("<.*?>")

client = ElevenLabs(
    api_key=os.environ["API_KEY"],  # Defaults to ELEVEN_API_KEY
)


def cleanhtml(raw_html):
    cleantext = re.sub(CLEANR, " ", raw_html)
    return cleantext.replace("&nbsp;", " ")


def convert_numbers_to_words(text):
    # Initialize inflect engine
    p = inflect.engine()

    # Regular expression to find numbers in the text
    pattern = r"\b\d+\b"

    # Find all numbers in the text
    numbers = re.findall(pattern, text)

    # Convert each number to words and replace in the text
    for num in numbers:
        num_word = p.number_to_words(num)
        text = text.replace(num, num_word)

    return text


def get_ssml(data):
    f = io.StringIO()
    with redirect_stdout(f):
        print("<speak>")
        for section in data["content"]:
            print(
                f" {convert_numbers_to_words(section['long_citation'].replace('.', ', paragraph '))} <break time='1000ms'/>"
            )
            if "question" in section:
                print(
                    f" {convert_numbers_to_words(section['question'].replace('?', ''))} "
                )
                print("<break time='500ms'/>")
                print(f" {section['answer']} <break time='1000ms'/>")
            else:
                print(f" {cleanhtml(section['body'])} <break time='1000ms'/>")

        print("</speak>")
    return f.getvalue()


# Takes ssml text as input, use AWS Polly to generate speech, and saves it to a file
def ssml_to_mp3(text, output_file):
    try:
        with open(output_file, "rb"):
            print(f"{output_file} already exists")
            return
    except FileNotFoundError:
        pass
    print(f"Generating {output_file}")
    audio = client.generate(
        text=text,
        voice="ZMZpwpXkV4GaVyJJXtJ3",
        model="eleven_multilingual_v2",
    )
    save(audio, output_file)
    with open(output_file.replace(".mp3", ".txt"), "w") as f:
        f.write(text)


for month in (
    "04",
    "05",
    "06",
    "03",
):  # , "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"):
    for day in range(1, 32):
        day = str(day).zfill(2)
        try:
            with open(f"content/{month}/{day}/data.json") as f:
                d = json.load(f)
        except FileNotFoundError:
            print(f"content/{month}/{day}/data.json not found")
            continue
        with open(f"content/{month}/{day}/data.json") as f:
            d = json.load(f)
        if (month, day) == ("07", "05"):
            d["content"][0]["answer"] = """
    For the right understanding of the Ten Commandments, these rules are to be observed:

    That the law is perfect, and bindeth every one to full conformity in the whole man unto the righteousness thereof, and unto entire obedience forever; so as to require the utmost perfection of every duty, and to forbid the least degree of every sin.

    That it is spiritual, and so reacheth the understanding, will, affections, and all other powers of the soul; as well as words, works, and gestures.

    That one and the same thing, in divers respects, is required or forbidden in several commandments.

    That as, where a duty is commanded, the contrary sin is forbidden; and, where a sin is forbidden, the contrary duty is commanded so, where a promise is annexed, the contrary threatening is included; and, where a threatening is annexed, the contrary promise is included.

    That what God forbids, is at no time to be done; what he commands, is always our duty; and yet every particular duty is not to be done at all times.

    That under one sin or duty, all of the same kind are forbidden or commanded; together with all the causes, means, occasions, and appearances thereof, and provocations thereunto.

    That what is forbidden or commanded to ourselves, we are bound, according to our places, to endeavor that it may be avoided or performed by others, according to the duty of their places.

    That in what is commanded to others, we are bound, according to our places and callings, to be helpful to them; and to take heed of partaking with others in what is forbidden them.
    """
        if (month, day) == ("01", "04"):
            d["content"][0]["body"] = """
    Under the name of Holy Scripture, or the Word of God written, are now contained all the books of the Old and New Testaments, which are these:

    OF THE OLD TESTAMENT

    Genesis
    Exodus
    Leviticus
    Numbers
    Deuteronomy
    Joshua
    Judges
    Ruth
    First Samuel
    Second Samuel
    First Kings
    Second Kings
    First Chronicles
    Second Chronicles
    Ezra
    Nehemiah
    Esther
    Jobe
    Psalms
    Proverbs
    Ecclesiastes
    The Song of Songs
    Isaiah
    Jeremiah
    Lamentations
    Ezekiel
    Daniel
    Hosea
    Joel
    Amos
    Obadiah
    Jonah
    Micah
    Nayhum
    Habakkuk
    Zephaniah
    Haggai
    Zechariah
    Malachi

    OF THE NEW TESTAMENT

    The Gospels according to
    Matthew
    Mark
    Luke
    John
    The Acts of the Apostles
    Paul’s Epistles
    to the Romans
    First Corinthians
    Second Corinthians
    Galatians
    Ephesians
    Colossians
    First Thessalonians
    Second Thessalonians
    The First Epistle to Timothy
    The Second Epistle to Timothy
    The Epistle to Titus
    The Epistle to Philemon
    The Epistle to the Hebrews
    The Epistle of James
    The first and second Epistles of Peter
    The first, second, and third Epistles of John
    The Epistle of Jude
    The Revelation of John

    All which are given by inspiration of God to be the rule of faith and life.
    """
        ssml = get_ssml(d)
        file = f"{month}{day}.mp3"
        ssml_to_mp3(
            ssml,
            f"output/{file}",
        )

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash,
                   session)
from flask_debugtoolbar import DebugToolbarExtension

from model import Decade, Country, Book, connect_to_db, db

import re
import pickle

from collections import Counter


app = Flask(__name__)

app.secret_key = "ABC"
app.jinja_env.undefined = StrictUndefined


def remove_irrelevant_characters(textstring):
    '''Removes commas, colons, semicolons, parentheses, double quotes, underscores, and
    asterisks from text. Replaces long dashes with a single space.'''

    textstring = re.sub(",|;|\*|_|\"|\(|\)|:|\”|\“", "", textstring)
    textstring = textstring.replace("—", " ")
    return textstring.replace("--", " ")


def make_unique_word_set(textstring):
    '''Removes all other punctuation and capitalization from string and returns set of unique words.'''

    textstring = re.sub("\.|\?|\!|…", "", textstring)
    textstring = textstring.lower()
    split_string = textstring.split()

    word_set = set(split_string)

    return word_set


def make_bigrams_and_frequencies(textstring):
    '''Returns dictionary of bigrams and their frequencies.'''

    split_string = textstring.split()

    bigram_frequencies = {}

    for i in range(0, (len(split_string)-1)):
        bigram = (split_string[i], split_string[i+1])

        if bigram in bigram_frequencies:
            bigram_frequencies[bigram] += 1

        else:
            bigram_frequencies[bigram] = 1

    return bigram_frequencies



def unpickle_data(filename):
    infile = open(filename, "rb")
    unpacked = pickle.load(infile)
    infile.close()
    return unpacked


@app.route('/')
def index():
    """Homepage."""
    decades = db.session.query(Decade.decade).all()
    formatted_decades = [decade[0] for decade in decades]

    return render_template("index.html", decades=formatted_decades)

@app.route("/methodology")
def show_methodology():
    return render_template("methodology.html")


@app.route('/process-text')
def analyze_text():
    textstring = remove_irrelevant_characters(request.args["textstring"])
    decade = request.args["decade"]
    books_from_decade = Book.query.filter_by(decade=decade).all()

    if books_from_decade == []:
        return render_template("no-corpus.html", decade=decade)

    else:

        if request.args["analysis-type"] == "words":
            words_in_passage = make_unique_word_set(textstring)

            comparison_set = set()

            for book in books_from_decade:
                wordset_file = book.word_set
                book_words = unpickle_data(wordset_file)
                comparison_set.update(book_words)

            anachronistic_words = words_in_passage - comparison_set
            anachronistic_words = sorted(list(anachronistic_words))

            if anachronistic_words == []:
                return render_template("words_results.html", decade=decade)

            else:
                return render_template("words_results.html", anachronistic_words=anachronistic_words, 
                    decade=decade)

        else:
            
            if request.args["analysis-type"] == "bigrams":
                bigrams_in_passage = make_bigrams_and_frequencies(textstring)

                comparison_dict = Counter({})

                for book in books_from_decade:
                    dict_file = book.bigram_dict
                    book_bigrams = Counter(unpickle_data(dict_file))
                    comparison_dict += book_bigrams

                comparison_results = {}

                for bigram in bigrams_in_passage:
                    appearances = comparison_dict.get(bigram, 0)
                    comparison_results[bigram] = appearances

                return render_template("bigrams_results.html", bigrams_in_passage=bigrams_in_passage, 
                    comparison_results=comparison_results, decade=decade)


if __name__ == "__main__":
    app.debug = True
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)
    DebugToolbarExtension(app)

    app.run(port=5000, host="0.0.0.0")
import csv
import random
import re

# Known abbreviations to skip
ABBREVIATIONS = {"JFK", "NBC", "NASA", "FBI", "USA"}


def random_omission(word):
    # E.g. "machine" -> "machne"
    if len(word) < 2:
        return word
    idx = random.randint(0, len(word) - 1)
    return word[:idx] + word[idx + 1 :]


def random_transposition(word):
    # E.g. "machine" -> "mahcine"
    if len(word) < 2:
        return word
    idx = random.randint(0, len(word) - 2)
    return word[:idx] + word[idx + 1] + word[idx] + word[idx + 2 :]


def random_repetition(word):
    # E.g. "machine" -> "macchine"
    if len(word) < 1:
        return word
    idx = random.randint(0, len(word) - 1)
    char_to_repeat = word[idx]
    return word[:idx] + char_to_repeat + word[idx:]


def phonetic_replacement(word):
    # Very simplistic approach, e.g. "ph" <-> "f", "c" <-> "k"
    # We'll just do one quick example
    replacements = [("ph", "f"), ("f", "ph"), ("c", "k"), ("k", "c")]
    # pick random rule
    (src, tgt) = random.choice(replacements)
    if src in word:
        word = word.replace(src, tgt, 1)
    return word


def generate_typos(query, n=3):
    """
    Generate n misspelling variants of the query.
    We'll do small random operations on separate words,
    skipping any known abbreviations.
    """
    words = query.split()
    variants = []

    for _ in range(n):
        new_words = []
        for w in words:
            # skip short words or known abbreviations
            if w.upper() in ABBREVIATIONS or len(w) < 3:
                new_words.append(w)
                continue
            # pick a random error type
            err_type = random.choice(
                [
                    random_omission,
                    random_transposition,
                    random_repetition,
                    phonetic_replacement,
                ]
            )
            new_word = err_type(w)
            new_words.append(new_word)
        variants.append(" ".join(new_words))
    return variants


def main():
    csv_path = "week-6/web_search_queries.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row["Query"]
            # example: 3 variants
            variants = generate_typos(query, n=3)
            print(f"\nOriginal: {query}")
            print("Misspellings:")
            for i, v in enumerate(variants, start=1):
                print(f"  {i}. {v}")


if __name__ == "__main__":
    main()

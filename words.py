# -*- coding: utf-8 -*-
"""Word bank for the Word Guessing Game.

Words are stored lowercase and contain only a-z so a single character
guess always maps to a letter. Adding words is safe: the game picks a
category first, then a word inside it, so categories stay a surprise.
"""

WORD_BANK = {
    "Animals": [
        "elephant", "giraffe", "penguin", "dolphin", "kangaroo",
        "squirrel", "butterfly", "crocodile", "octopus", "hedgehog",
        "leopard", "flamingo", "cheetah", "raccoon", "otter",
    ],
    "Food": [
        "chocolate", "pineapple", "spaghetti", "pancake", "avocado",
        "raspberry", "cinnamon", "broccoli", "mushroom", "lemonade",
        "cupcake", "pretzel", "omelette", "pumpkin", "yoghurt",
    ],
    "Nature": [
        "mountain", "volcano", "rainbow", "forest", "glacier",
        "thunder", "meadow", "cactus", "island", "sunflower",
        "waterfall", "lavender", "horizon", "pebble", "canyon",
    ],
    "Technology": [
        "computer", "keyboard", "algorithm", "database", "firewall",
        "monitor", "satellite", "browser", "software", "network",
        "pixel", "router", "compiler", "terminal", "variable",
    ],
    "Places": [
        "library", "museum", "stadium", "harbour", "castle",
        "pyramid", "lighthouse", "market", "bakery", "theatre",
        "airport", "cabin", "temple", "bridge", "tower",
    ],
    "Music": [
        "guitar", "trumpet", "melody", "harmony", "orchestra",
        "rhythm", "saxophone", "violin", "concert", "chorus",
        "drummer", "piano", "ballad", "tempo", "anthem",
    ],
}


def all_words():
    """Return a list of every (word, category) pair in the bank."""
    pairs = []
    for category, items in WORD_BANK.items():
        for word in items:
            pairs.append((word, category))
    return pairs

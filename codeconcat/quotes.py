import random

# Programming quotes and their catified versions
QUOTES = [
    (
        "Clean code always looks like it was written by someone who cares. - Robert C. Martin",
        "A well-groomed cat always looks like it belongs to someone who cares. - Robert C. Meowtin",
    ),
    (
        "First, solve the problem. Then write the code. - John Johnson",
        "First, locate the sunbeam. Then take the nap. - John Purrson",
    ),
    (
        "Any fool can write code that a computer can understand. Good programmers write code that humans can understand. - Martin Fowler",
        "Any cat can meow to be fed. Good cats communicate in ways their humans can understand. - Meowin Prowler",
    ),
    (
        "Programming isn't about what you know; it's about what you can figure out. - Chris Pine",
        "Cat life isn't about what territories you own; it's about what furniture you can claim. - Whiskers Fine",
    ),
    (
        "Code is like humor. When you have to explain it, it's bad. - Cory House",
        "Cat behavior is like humor. When you have to explain it, it's missed its mark. - Clawry Mouse",
    ),
    (
        "The most important property of a program is whether it accomplishes the intention of its user. - C.A.R. Hoare",
        "The most important quality of a cat is whether it accomplishes the intention of looking adorable while doing whatever it wants. - C.A.T. Purr",
    ),
    (
        "Good code is its own best documentation. As you're about to add a comment, ask yourself, 'How can I improve the code so that this comment isn't needed?' - Steve McConnell",
        "Good cat behavior is its own reward. As you're about to scold your cat, ask yourself, 'How can I arrange my home so this scolding isn't needed?' - Steve McGrowl",
    ),
    (
        "Measuring programming progress by lines of code is like measuring aircraft building progress by weight. - Bill Gates",
        "Measuring a cat's happiness by hours of sleep is like measuring its hunting skill by weight of prey. - Bill Cats",
    ),
    (
        "Talk is cheap. Show me the code. - Linus Torvalds",
        "Meow is cheap. Show me the treat. - Linus Pawvalds",
    ),
    (
        "Truth can only be found in one place: the code. - Robert C. Martin",
        "Truth can only be found in one place: the purr. - Robert C. Meowtin",
    ),
    (
        "It is not enough for code to work. - Robert C. Martin",
        "It is not enough for a cat to exist - it must be admired. - Robert C. Meowtin",
    ),
    (
        "Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it. - Brian W. Kernighan",
        "Cleaning up after a cat is twice as hard as getting a cat in the first place. Therefore, if you get the most mischievous cat possible, you are, by definition, not prepared enough to handle the chaos. - Brian W. Kittyghan",
    ),
    (
        "Sometimes it pays to stay in bed on Monday rather than spending the rest of the week debugging Monday's code. - Dan Salomon",
        "Sometimes it pays to stay curled up on the couch rather than spending the rest of the day exploring that suspicious noise. - Dan Salmeowin",
    ),
    (
        "Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live. - Rick Osborne",
        "Always behave as if the human who fills your food bowl will remember every hairball you've left on their pillow. - Rick Pawsborne",
    ),
]


def get_random_quote(catify: bool = None) -> str:
    """
    Returns a random programming quote or its catified version.
    If catify is None, randomly chooses normal or cat version.
    """
    quote, cat_quote = random.choice(QUOTES)
    if catify is None:
        catify = random.choice([True, False])
    return cat_quote if catify else quote

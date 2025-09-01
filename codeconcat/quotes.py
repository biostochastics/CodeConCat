import random
from typing import Optional

# Programming quotes and their catified versions - Refined collection of 50 pairs
QUOTES = [
    # Category: Core Principles & Truths (The "Perfect" Five)
    (
        "Software is a gas; it expands to fill its container. - Nathan Myhrvold",
        "A cat is a liquid; it expands to fill any box provided. - Nathan Purrvold",
    ),
    (
        "There are only two hard things in Computer Science: cache invalidation and naming things. - Phil Karlton",
        "There are only two hard things in Cat Science: nap spot invalidation and naming kittens. - Phil Pawlton",
    ),
    (
        "Some people, when confronted with a problem, think 'I know, I'll use regular expressions.' Now they have two problems. - Jamie Zawinski",
        "Some cats, when confronted with a closed door, think 'I know, I'll meow loudly.' Now they have angry humans. - Jamie Clawinski",
    ),
    (
        "Talk is cheap. Show me the code. - Linus Torvalds",
        "Meow is cheap. Show me the treat. - Linus Pawvalds",
    ),
    (
        "Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it. - Brian W. Kernighan",
        "Cleaning up after a cat is twice as hard as getting a cat in the first place. Therefore, if you get the most mischievous cat possible, you are, by definition, not prepared enough to handle the chaos. - Brian W. Kittyghan",
    ),
    # Category: Refined & Polished
    (
        "Clean code always looks like it was written by someone who cares. - Robert C. Martin",
        "A clean litter box always looks like it was maintained by someone who values their ankles. - Robert C. Meowtin",
    ),
    (
        "First, solve the problem. Then write the code. - John Johnson",
        "First, stare at the problem. Then knock it off the table. - John Purrson",
    ),
    (
        "Truth can only be found in one place: the code. - Robert C. Martin",
        "Truth can only be found in one place: the empty food bowl at 3 AM. - Robert C. Meowtin",
    ),
    (
        "Programs must be written for people to read, and only incidentally for machines to execute. - Harold Abelson",
        "A tail must be flicked for humans to read; internal annoyance is insufficient. - Harold Apawlson",
    ),
    # Category: Development Process & Philosophy
    (
        "The first 90 percent of the code accounts for the first 90 percent of the development time. The remaining 10 percent of the code accounts for the other 90 percent of the development time. - Tom Cargill",
        "The first 90 percent of the nap uses the first 90 percent of the sunbeam. The remaining 10 percent of the nap chases the other 90 percent of the sunbeam's movement. - Tom Catgill",
    ),
    (
        "It's not a bug – it's an undocumented feature. - Anonymous",
        "It's not knocking things over – it's gravity testing. - Anonymouse",
    ),
    (
        "It works on my machine. - Every Developer",
        "It was comfortable on my human. - Every Cat",
    ),
    (
        "If it's a good idea, go ahead and do it. It's much easier to apologize than it is to get permission. - Grace Hopper",
        "If the glass is full, go ahead and knock it over. It's much easier to look cute than to get permission. - Grace Pawper",
    ),
    (
        "Don't Repeat Yourself (DRY). - Andy Hunt and Dave Thomas",
        "Always Repeat Yourself (ARY), especially at 3 AM for food. - Andy Hunt and Dave Tomcat",
    ),
    (
        "You Aren't Gonna Need It (YAGNI). - Extreme Programming",
        "You Aren't Gonna Eat It (but I'll bat it under the fridge just in case). - Extreme Catting",
    ),
    (
        "Walking on water and developing software from a specification are easy if both are frozen. - Edward V. Berard",
        "Sitting still and tolerating a belly rub are easy if the cat is asleep. - Edward V. Purrard",
    ),
    (
        "Adding manpower to a late software project makes it later. - Fred Brooks",
        "Adding another cat to a stable cat household makes the first cat angrier. - Fred Purooks",
    ),
    (
        "Measuring programming progress by lines of code is like measuring aircraft building progress by weight. - Bill Gates",
        "Measuring a cat's affection by number of purrs is like measuring a nap's quality by its duration. - Bill Cats",
    ),
    (
        "The best way to get a project done faster is to start sooner. - Jim Highsmith",
        "The best way to get breakfast served faster is to start meowing sooner. - Jim Meowsmith",
    ),
    (
        "Code is read more often than it is written. - Guido van Rossum",
        "The food bowl is stared at more often than it is eaten from. - Guido van Possum",
    ),
    # Category: Code Quality & Design
    (
        "Good code is its own best documentation. As you're about to add a comment, ask yourself, 'How can I improve the code so that this comment isn't needed?' - Steve McConnell",
        "A well-placed hairball is its own best explanation. As you're about to justify it, ask yourself, 'How can I position it so that its purpose is obvious?' - Steve McGrowl",
    ),
    (
        "Simplicity is the ultimate sophistication. - Leonardo da Vinci",
        "An empty cardboard box is the ultimate luxury. - Leonardo da Kittci",
    ),
    (
        "The function of good software is to make the complex appear to be simple. - Grady Booch",
        "The function of a good cat is to make the complex act of opening a can appear to be a simple, required daily tribute. - Grady Pooch",
    ),
    (
        "Before software can be reusable it first has to be usable. - Ralph Johnson",
        "Before a lap can be re-napped-on, it first has to be comfortable. - Ralph Clawnson",
    ),
    (
        "Any fool can write code that a computer can understand. Good programmers write code that humans can understand. - Martin Fowler",
        "Any cat can make noise. A good cat makes a specific noise that its human understands is for 'the expensive wet food, not the dry stuff.' - Meowin Prowler",
    ),
    (
        "Simplicity is a prerequisite for reliability. - Edsger W. Dijkstra",
        "A sunbeam is a prerequisite for a reliable nap. - Edsger W. Catstra",
    ),
    (
        "Legacy code is code without tests. - Michael Feathers",
        "Forgotten furniture is furniture without scratch marks. - Michael Feathers",
    ),
    (
        "Refactoring is the process of changing a software system in such a way that it does not alter the external behavior of the code, yet improves its internal structure. - Martin Fowler",
        "Grooming is the process of changing a cat's fur in such a way that it does not alter the cat's external sleepiness, yet improves its internal sense of superiority. - Meowin Prowler",
    ),
    # Category: Famous Names & Puns
    (
        "Given enough eyeballs, all bugs are shallow. - Linus Torvalds",
        "Given enough intense staring, all humans will eventually surrender their food. - Lynx Torvalds",
    ),
    (
        "Premature optimization is the root of all evil. - Donald Knuth",
        "A premature pounce is the root of all missed red dots. - Donald Mewth",
    ),
    (
        "Computer science is no more about computers than astronomy is about telescopes. - Edsger W. Dijkstra",
        "Sleeping is no more about being tired than sitting on a laptop is about using a computer. - Edsger Catstra",
    ),
    (
        "Fools ignore complexity. Pragmatists suffer it. Some can avoid it. Geniuses remove it. - Alan Perlis",
        "Fools ignore the red dot. Pragmatists chase it. Some can catch it. Geniuses wait for it to land on the human's face. - Alan Purrlis",
    ),
    (
        "The most important property of a program is whether it accomplishes the intention of its user. - C.A.R. Hoare",
        "The most important property of a human is whether they accomplish the intention of their cat. - C.A.T. Hoare",
    ),
    # Category: The Wider World of Tech & Cats
    (
        "The cloud is just someone else's computer. - Chris Watterston",
        "The food bowl is just the human's delayed-action hand. - Chris Catterston",
    ),
    (
        "In theory, theory and practice are the same. In practice, they are not. - Yogi Berra",
        "In theory, a closed door is a barrier. In practice, it is a personal insult. - Yogi Purra",
    ),
    (
        "The best error message is the one that never shows up. - Thomas Fuchs",
        "The best sign of displeasure is the one the human only discovers by smell. - Thomas Hiss",
    ),
    (
        "A user interface is like a joke. If you have to explain it, it's not that good. - Martin LeBlanc",
        "A request for food is like a stare. If you have to meow, the human isn't that good. - Martin LePounce",
    ),
    (
        "A good programmer is someone who always looks both ways before crossing a one-way street. - Doug Linder",
        "A good cat is one who checks for a second human to beg from after the first one says no. - Doug Whisker",
    ),
    (
        "There are two ways of constructing a software design: make it so simple that there are obviously no deficiencies, or make it so complicated that there are no obvious deficiencies. - C.A.R. Hoare",
        "There are two ways to get a treat: be so cute there is obviously no reason to deny you, or be so annoying there are no obvious alternatives to giving you one. - C.A.T. Hoare",
    ),
    (
        "Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live. - Rick Osborne",
        "Always nap as if the thing that ends up waking you will be a violent vacuum cleaner that knows where you sleep. - Rick Pawsborne",
    ),
    (
        "The trouble with programmers is that you can never tell what a programmer is doing until it's too late. - Seymour Cray",
        "The trouble with cats is that you can never tell what a cat is thinking until the vase is already on the floor. - Seymour Tray",
    ),
    (
        "Programming isn't about what you know; it's about what you can figure out. - Chris Pine",
        "Hunting isn't about what you see; it's about what you can hear rustling under the couch. - Whiskers Fine",
    ),
    (
        "The best performance improvement is the transition from the nonworking state to the working state. - J. Osterhout",
        "The best comfort improvement is the transition from a non-napping state to a napping-on-fresh-laundry state. - J. Posterhout",
    ),
    (
        "The goal of Computer Science is to build something that will last at least until we've finished building it. - Anonymous",
        "The goal of a Cat is to nap on something that will stay warm at least until we've finished napping on it. - Anonymouse",
    ),
    (
        "To iterate is human, to recurse divine. - L. Peter Deutsch",
        "To stretch is feline, to nap divine. - L. Peter Scratch",
    ),
    (
        "A specification that will not fit on one page of 8.5x11 inch paper cannot be understood. - Mark Ardis",
        "A box that I do not fit in cannot be sat in. I will sit in it anyway. - Mark Pawdis",
    ),
    (
        "Make it work, make it right, make it fast. - Kent Beck",
        "Wake them up, get it fed, go to sleep. - Kent Peck",
    ),
    (
        "Documentation is the castor oil of programming. Managers think it is good for programmers and programmers hate it. - Gerald Weinberg",
        "A collar is the castor oil of cat ownership. Humans think it is good for cats and cats hate it. - Gerald Whiskberg",
    ),
    (
        "What one programmer can do in one month, two programmers can do in two months. - Fred Brooks",
        "What one cat can knock over in one minute, two cats can knock over in thirty seconds. - Fred Purooks",
    ),
    (
        "A program that produces incorrect results twice as fast is infinitely slower. - Anonymous",
        "A human who fills the wrong food bowl twice as fast is infinitely more useless. - Anonymouse",
    ),
]


def get_random_quote(catify: Optional[bool] = None) -> str:
    """
    Returns a random programming quote or its catified version.
    If catify is None, randomly chooses normal or cat version.
    """
    quote, cat_quote = random.choice(QUOTES)
    if catify is None:
        catify = random.choice([True, False])
    return cat_quote if catify else quote

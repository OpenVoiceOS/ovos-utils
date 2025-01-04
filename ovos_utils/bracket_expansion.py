import itertools
import re
from typing import List, Dict
import warnings
from ovos_utils.log import deprecated


def expand_template(template: str) -> List[str]:
    def expand_optional(text):
        """Replace [optional] with two options: one with and one without."""
        return re.sub(r"\[([^\[\]]+)\]", lambda m: f"({m.group(1)}|)", text)

    def expand_alternatives(text):
        """Expand (alternative|choices) into a list of choices."""
        parts = []
        for segment in re.split(r"(\([^\(\)]+\))", text):
            if segment.startswith("(") and segment.endswith(")"):
                options = segment[1:-1].split("|")
                parts.append(options)
            else:
                parts.append([segment])
        return itertools.product(*parts)

    def fully_expand(texts):
        """Iteratively expand alternatives until all possibilities are covered."""
        result = set(texts)
        while True:
            expanded = set()
            for text in result:
                options = list(expand_alternatives(text))
                expanded.update(["".join(option).strip() for option in options])
            if expanded == result:  # No new expansions found
                break
            result = expanded
        return sorted(result)  # Return a sorted list for consistency

    # Expand optional items first
    template = expand_optional(template)

    # Fully expand all combinations of alternatives
    return fully_expand([template])


def expand_slots(template: str, slots: Dict[str, List[str]]) -> List[str]:
    """Expand a template by first expanding alternatives and optional components,
    then substituting slot placeholders with their corresponding options.

    Args:
        template (str): The input string template to expand.
        slots (dict): A dictionary where keys are slot names and values are lists of possible replacements.

    Returns:
        list[str]: A list of all expanded combinations.
    """
    # Expand alternatives and optional components
    base_expansions = expand_template(template)

    # Process slots
    all_sentences = []
    for sentence in base_expansions:
        matches = re.findall(r"\{([^\{\}]+)\}", sentence)
        if matches:
            # Create all combinations for slots in the sentence
            slot_options = [slots.get(match, [f"{{{match}}}"]) for match in matches]
            for combination in itertools.product(*slot_options):
                filled_sentence = sentence
                for slot, replacement in zip(matches, combination):
                    filled_sentence = filled_sentence.replace(f"{{{slot}}}", replacement)
                all_sentences.append(filled_sentence)
        else:
            # No slots to expand
            all_sentences.append(sentence)

    return all_sentences


@deprecated("use 'expand_template' directly instead", "1.0.0")
def expand_parentheses(sent: List[str]) -> List[str]:
    """
    ['1', '(', '2', '|', '3, ')'] -> [['1', '2'], ['1', '3']]
    For example:
    Will it (rain|pour) (today|tomorrow|)?
    ---->
    Will it rain today?
    Will it rain tomorrow?
    Will it rain?
    Will it pour today?
    Will it pour tomorrow?
    Will it pour?
    Args:
        sent (list<str>): List of tokens in sentence
    Returns:
        list<list<str>>: Multiple possible sentences from original
    """
    warnings.warn(
        "use 'expand_template'",
        DeprecationWarning,
        stacklevel=2,
    )
    return SentenceTreeParser(sent).expand_parentheses()


@deprecated("use 'expand_template' directly instead", "1.0.0")
def expand_options(parentheses_line: str) -> list:
    """
    Convert 'test (a|b)' -> ['test a', 'test b']
    Args:
        parentheses_line: Input line to expand
    Returns:
        List of expanded possibilities
    """
    warnings.warn(
        "use 'expand_template'",
        DeprecationWarning,
        stacklevel=2,
    )
    # 'a(this|that)b' -> [['a', 'this', 'b'], ['a', 'that', 'b']]
    options = expand_parentheses(re.split(r'([(|)])', parentheses_line))
    return [re.sub(r'\s+', ' ', ' '.join(i)).strip() for i in options]


class Fragment:
    """(Abstract) empty sentence fragment"""

    @deprecated("use 'expand_template' function directly instead", "1.0.0")
    def __init__(self, tree):
        """
        Construct a sentence tree fragment which is merely a wrapper for
        a list of Strings
        Args:
            tree (?): Base tree for the sentence fragment, type depends on
                        subclass, refer to those subclasses
        """
        warnings.warn(
            "use 'expand_template'",
            DeprecationWarning,
            stacklevel=2,
        )
        self._tree = tree

    def tree(self):
        """Return the represented sentence tree as raw data."""
        return self._tree

    def expand(self):
        """
        Expanded version of the fragment. In this case an empty sentence.
        Returns:
            List<List<str>>: A list with an empty sentence (= token/string list)
        """
        return [[]]

    def __str__(self):
        return self._tree.__str__()

    def __repr__(self):
        return self._tree.__repr__()


class Word(Fragment):
    """
    Single word in the sentence tree.
    Construct with a string as argument.
    """

    @deprecated("use 'expand_template' function directly instead", "1.0.0")
    def __init__(self, tree):
        """DEPRECATED"""
        warnings.warn(
            "use 'expand_template'",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(tree)

    def expand(self):
        """
        Creates one sentence that contains exactly that word.
        Returns:
            List<List<str>>: A list with the given string as sentence
                                (= token/string list)
        """
        return [[self._tree]]


class Sentence(Fragment):
    """
    A Sentence made of several concatenations/words.
    Construct with a List<Fragment> as argument.
    """

    @deprecated("use 'expand_template' function directly instead", "1.0.0")
    def __init__(self, tree):
        """DEPRECATED"""
        warnings.warn(
            "use 'expand_template'",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(tree)

    def expand(self):
        """
        Creates a combination of all sub-sentences.
        Returns:
            List<List<str>>: A list with all subsentence expansions combined in
                                every possible way
        """
        old_expanded = [[]]
        for sub in self._tree:
            sub_expanded = sub.expand()
            new_expanded = []
            while len(old_expanded) > 0:
                sentence = old_expanded.pop()
                for new in sub_expanded:
                    new_expanded.append(sentence + new)
            old_expanded = new_expanded
        return old_expanded


class Options(Fragment):
    """
    A Combination of possible sub-sentences.
    Construct with List<Fragment> as argument.
    """

    @deprecated("use 'expand_template' function directly instead", "1.0.0")
    def __init__(self, tree):
        """DEPRECATED"""
        warnings.warn(
            "use 'expand_template'",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(tree)

    def expand(self):
        """
        Returns all of its options as seperated sub-sentences.
        Returns:
            List<List<str>>: A list containing the sentences created by all
                                expansions of its sub-sentences
        """
        options = []
        for option in self._tree:
            options.extend(option.expand())
        return options


class SentenceTreeParser:
    """
    Generate sentence token trees from a list of tokens
    ['1', '(', '2', '|', '3, ')'] -> [['1', '2'], ['1', '3']]
    """

    @deprecated("use 'expand_template' function directly instead", "1.0.0")
    def __init__(self, tokens):
        warnings.warn(
            "use 'expand_template'",
            DeprecationWarning,
            stacklevel=2,
        )
        self.tokens = tokens

    def _parse(self):
        """
        Generate sentence token trees
        ['1', '(', '2', '|', '3, ')'] -> ['1', ['2', '3']]
        """
        self._current_position = 0
        return self._parse_expr()

    def _parse_expr(self):
        """
        Generate sentence token trees from the current position to
        the next closing parentheses / end of the list and return it
        ['1', '(', '2', '|', '3, ')'] -> ['1', [['2'], ['3']]]
        ['2', '|', '3'] -> [['2'], ['3']]
        """
        # List of all generated sentences
        sentence_list = []
        # Currently active sentence
        cur_sentence = []
        sentence_list.append(Sentence(cur_sentence))
        # Determine which form the current expression has
        while self._current_position < len(self.tokens):
            cur = self.tokens[self._current_position]
            self._current_position += 1
            if cur == '(':
                # Parse the subexpression
                subexpr = self._parse_expr()
                # Check if the subexpression only has one branch
                # -> If so, append "(" and ")" and add it as is
                normal_brackets = False
                if len(subexpr.tree()) == 1:
                    normal_brackets = True
                    cur_sentence.append(Word('('))
                # add it to the sentence
                cur_sentence.append(subexpr)
                if normal_brackets:
                    cur_sentence.append(Word(')'))
            elif cur == '|':
                # Begin parsing a new sentence
                cur_sentence = []
                sentence_list.append(Sentence(cur_sentence))
            elif cur == ')':
                # End parsing the current subexpression
                break
            # TODO anything special about {sth}?
            else:
                cur_sentence.append(Word(cur))
        return Options(sentence_list)

    def _expand_tree(self, tree):
        """
        Expand a list of sub sentences to all combinated sentences.
        ['1', ['2', '3']] -> [['1', '2'], ['1', '3']]
        """
        return tree.expand()

    def expand_parentheses(self):
        tree = self._parse()
        return self._expand_tree(tree)

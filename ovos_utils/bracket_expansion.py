import itertools
import re
from typing import List, Dict

from ovos_spec_tools import expand as _spec_expand


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
    base_expansions = sorted(_spec_expand(template))

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

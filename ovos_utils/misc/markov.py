import random
import json


class MarkovChain:
    """
    Simple Markov Chain Class
    """
    START_OF_SEQ = "~"
    END_OF_SEQ = "[END]"

    def __init__(self, order=1, pad=True, records=None):
        """
        Initialise Markov chain
        :param order: int - number of tokens to consider a state
        :param pad: bool - whether to pad training strings with start/end tokens
        """
        self.order = order
        self.pad = pad
        self.records = {} if records is None else records

    def add_tokens(self, tokens):
        """
        Adds a list of tokens to the markov chain
        :param tokens: list of tokens
        :return: None
        """
        if self.pad:
            tokens = [self.START_OF_SEQ] * self.order + tokens + [
                self.END_OF_SEQ]

        for i in range(len(tokens) - self.order):
            current_state = tuple(tokens[i:i + self.order])
            next_state = tokens[i + self.order]
            self.add_state(current_state, next_state)

    def add_state(self, current_state, next_state):
        """
        Updates the weight of the transition from current_state to next_state
        with a single observation.
        :param current_state: tuple - current state
        :param next_state: token - the next observed token
        :return: None
        """
        if current_state not in self.records.keys():
            self.records[current_state] = dict()

        if next_state not in self.records[current_state].keys():
            self.records[current_state][next_state] = 0

        self.records[current_state][next_state] += 1

    def generate_sequence(self, n=100, initial_state=None):
        """
        Generates a sequence of tokens from the markov chain, starting from
        initial_state. If initial state is empty, and pad is false it chooses an
        initial state at random. If pad is true,
        :param n: int - The number of tokens to generate
        :param initial_state: starting state of the generator
        :return: list of generated tokens
        """

        if initial_state is None:
            if self.pad:
                sequence = [START_OF_SEQ] * self.order
            else:
                sequence = list(random.choice(self.records.keys()))
        else:
            sequence = initial_state[:]

        for i in range(n):
            current_state = tuple(sequence[-self.order:])
            next_token = self.sample(current_state)
            sequence.append(next_token)

            if next_token == self.END_OF_SEQ:
                return sequence

        return sequence

    def sample(self, current_state, random_on_fail=True):
        """
        Generates a random next token, given current_state
        :param current_state: tuple - current_state
        :return: token
        """
        if current_state not in self.records.keys() and random_on_fail:
            current_state = random.choice(self.records.keys())

        possible_next = self.records[current_state]
        n = sum(possible_next.values())

        m = random.randint(0, n)
        count = 0
        for k, v in possible_next.items():
            count += v
            if m <= count:
                return k

    def save(self, filename):
        """
        Saves Markov chain to filename
        :param filename: string - where to save chain
        :return: None
        """
        with open(filename, "w") as f:
            m = {
                "order": self.order,
                "pad": self.pad,
                "records": {str(k): v for k, v in self.records.items()}
            }
            json.dump(m, f)

    @staticmethod
    def load(filename):
        """
        Loads Markov chain from json file
        DUE TO USE OF EVAL
        DO NOT RUN THIS ON UNTRUSTED FILES
        :param filename:
        :return: MarkovChain
        """
        with open(filename, "r") as f:
            raw = json.load(f)

        mc = MarkovChain(
            raw["order"],
            raw["pad"],
            {eval(k): v for k, v in raw["records"].items()}
        )

        return mc

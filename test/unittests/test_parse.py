import unittest
from ovos_utils.parse import remove_parentheses, summarize, search_in_text, \
    extract_paragraphs, extract_sentences, split_sentences, singularize


class TestParseHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.test_string = "Mr. Smith bought cheapsite.com for 1.5 million dollars, i.e. he paid a lot for it. Did he mind? Adam Jones Jr. thinks he didn't. In any case, this isn't true... Well, with a probability of .9 it isn't.I know right\nOK"
        self.wiki_dump = """Mycroft is a free and open-source voice assistant for Linux-based operating systems that uses a natural language user interface. Its code was formerly copyleft, but is now under a permissive license.

History
Inspiration for Mycroft came when Ryan Sipes and Joshua Montgomery were visiting the Kansas City makerspace, where they came across a simple and basic intelligent virtual assistant project. They were interested in the technology, but did not like its inflexibility. Montgomery believes that the burgeoning industry of intelligent personal assistance poses privacy concerns for users and has promised that Mycroft will protect privacy through its open source machine learning platform. Mycroft has won several awards including the prestigious Techweek's KC Launch competition in 2016. Mycroft was part of the Sprint Accelerator 2016 class in Kansas City and joined 500 Startups Batch 20 in February 2017. The company accepted a strategic investment from Jaguar Land Rover during this same time period. To date, the company has raised more than $2.5 million from institutional investors and has opted to offer shares of the company to the public through Startengine, an equity crowdfunding platform. It is named after a fictional computer from 1966 science fiction novel The Moon Is a Harsh Mistress.

Mycroft voice stack
Mycroft provides open source software for most parts of the voice stack.

Wake Word
Mycroft does Wake Word spotting, also called keyword spotting, through its Precise Wake Word engine. Prior to Precise becoming the default Wake Word engine, Mycroft employed PocketSphinx. Instead of being based on phoneme recognition, Precise uses a trained recurrent neural network to distinguish between sounds which are, and which aren't Wake Words.

Speech to text
Mycroft is partnering with Mozilla's Common Voice Project to leverage their DeepSpeech speech to text software.

Intent parsing
Mycroft uses an intent parser called Adapt to convert natural language into machine-readable data structures. Adapt undertakes intent parsing by matching specific keywords in an order within an utterance. They also have a parser, Padatious. Padatious, in contrast, uses example-based inference to determine intent.

Text to speech
For speech synthesis Mycroft uses Mimic, which is based on the Festival Lite speech synthesis system.

Modular design and interoperability
Mycroft is designed to be modular, so users are able to change its components. For example, espeak can be used instead of Mimic.

Hardware
The Mycroft project is also working on and selling smart speakers that run its software. All of its hardware is open-source, released under the CERN Open Hardware Licence.Its first hardware project was the Mark I, targeted primarily at developers. Its production was partially funded through a Kickstarter campaign, which finished successfully. Units started shipping out in April 2016.Its most recent hardware project is the Mark II, intended for general usage, not just for developers. Unlike the Mark I, the Mark II is equipped with a screen, being able to relay information both visually as well as acoustically. As with the Mark I, the Mark II's production will be partially funded through a Kickstarter campaign, which wrapped up in February 2018, hitting almost 8 times its original goal.Mycroft announced that a third hardware project, Mark III, will be offered through Kickstarter, and that an entire product line of Mark I, II, and III will be released to stores by November, 2019.

Partnerships
Mycroft has undertaken several commercial collaborations. In May 2018, the company partnered with WorkAround, an impact sourcing provider who broker work opportunities for refugees, to undertake bulk machine learning training. In October 2018, Mycroft collaborated with disease surveillance and forecasting company, SickWeather, to identify the frequency of coughing on public transport, funded by the City of Kansas City, Missouri.

See also

Amazon Alexa
Cortana
Google Assistant
Siri


== References ==
    """

    def test_singularize(self):
        # uses inflection module for english
        # https://pypi.org/project/inflection/
        self.assertEqual(
            singularize("dogs"), "dog"
        )
        self.assertEqual(
            singularize("dogs", "en"), "dog"
        )

        # failure cases, just strips "s"
        self.assertEqual(
            singularize("cães", "pt"), "cãe"
        )
        self.assertEqual(
            singularize("cães", "es"), "cãe"
        )

    # TODO fix me
    """
    def test_split_sentences(self):
        # no split
        self.assertEqual(split_sentences("A.E:I.O.U"), [])
        self.assertEqual(split_sentences("hello.com"), [])

        # ambiguous, nosplit
        self.assertEqual(split_sentences("hello. he said"), [])
        self.assertEqual(split_sentences("hello.he said"), [])
        # TODO maybe split this one?
        self.assertEqual(split_sentences("hello . he said"), [])

        # ambiguous, but will split
        self.assertEqual(
            split_sentences("hello.He said"),
            ["hello", "He said"]
        )

        # split at periods
        self.assertEqual(
            split_sentences("hello. He said"),
            ["hello", "He said"]
        )
        self.assertEqual(
            split_sentences("hello . He said"),
            ["hello", "He said"]
        )

    # TODO fix me
    def test_summarize(self):
        self.assertEqual(
            extract_paragraphs("precise", self.wiki_dump),
            []
        )
        self.assertEqual(
            extract_sentences("intent", self.wiki_dump),
            []
        )
        self.assertEqual(summarize(self.test_string), "")
    """

from ovos_utils.lang import detect_lang, translate_text

# detecting language
detect_lang("olá eu chamo-me joaquim")  # "pt"
detect_lang("olá eu chamo-me joaquim", return_dict=True)
"""{'confidence': 0.9999939001351439, 'language': 'pt'}"""

detect_lang("hello world")  # "en"
detect_lang("This piece of text is in English. Този текст е на Български.", return_dict=True)
"""{'confidence': 0.28571342657428966, 'language': 'en'}"""

# translating text
#  - source lang will be auto detected using utils above
#  - default target language is english
translate_text("olá eu chamo-me joaquim")
"""Hello I call myself joaquim"""

#  - you should specify source lang whenever possible to save 1 api call
translate_text("olá eu chamo-me joaquim", source_lang="pt", lang="es")
"""Hola, me llamo Joaquim"""

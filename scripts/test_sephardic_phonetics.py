import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_sephardic_phonetics import transliterate_text


class SephardicPhoneticsTests(unittest.TestCase):
    def test_examples(self):
        cases = {
            "בְּרֵאשִׁית": "bereshit",
            "כָּל": "kol",
            "חָכְמָה": "jojmá",
            "וּבְחַיֵּי": "uvejaié",
            "בֵּין": "ben",
            "יִשְׂרָאֵל": "israel",
            "בַּעֲגָלָא": "baagalá",
            "בָּרָא֖": "bará",
            "שָׁמְרָה": "shomrá",
            "שָֽׁמְרָה": "shámera",
            "כָּל־הָאָרֶץ": "kol-haaretz",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate_text(source), expected)


if __name__ == "__main__":
    unittest.main()

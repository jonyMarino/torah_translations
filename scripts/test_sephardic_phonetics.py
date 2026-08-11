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
            "בָּנָיו": "banav",
            "נַפְשְׁךָ": "nafshejá",
            "הִנְנִי": "hinení",
            "לֹמְדִים": "lomedim",
            "יְהוָה": "adonai",
            "יֱהֹוִה": "adonai",
            "בַּיהוָה": "badonai",
            "לַיהוָה": "ladonai",
            "בַּעֲגָלָא": "ba'agalá",
            "בָּרָא֖": "bará",
            "שָׁמְרָה": "shomrá",
            "שָֽׁמְרָה": "shámera",
            "לָ֑ךְ": "laj",
            "הַמָּק֖וֹם": "hamakom",
            "עַל": "'al",
            "שְׁעָרֶ֙יךָ֙": "she'areja",
            "כָּל־הָאָרֶץ": "kol-haaretz",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(transliterate_text(source), expected)


if __name__ == "__main__":
    unittest.main()

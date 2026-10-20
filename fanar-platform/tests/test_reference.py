import unittest

from fanar.reference.service import LocalReferenceSource, ManarReferenceSource, ReferenceService


class TestReference(unittest.TestCase):
    def setUp(self):
        self.svc = ReferenceService(LocalReferenceSource())

    def test_fund_range(self):
        codes = {f.code for f in self.svc.funds()}
        self.assertEqual(len(codes), 6)
        self.assertIn("3983", codes)

    def test_codifications(self):
        codes = [c.code for c in self.svc.codifications("MonetaireBaseCalcul")]
        self.assertIn("R/360", codes)

    def test_manar_source_maps_poste(self):
        class FakeManar:
            def query(self, op, params=None, body=None):
                if op == "reference.posting_rules":
                    return [{"code": "REPOO", "label": "Repo", "classe": "OBL",
                             "flagRepo": "O", "decalageLivraison": "0", "posteMiroir": "M1"}]
                return []

        rules = ManarReferenceSource(FakeManar()).posting_rules()
        self.assertEqual(rules[0].code, "REPOO")
        self.assertTrue(rules[0].repo_flag)
        self.assertEqual(rules[0].mirror_post, "M1")


if __name__ == "__main__":
    unittest.main()

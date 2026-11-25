import unittest,sys,tempfile,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from core import db_open,normalize_domain,import_domains,extract_prices,followup_due
class CoreTests(unittest.TestCase):
 def test_normalize(self): self.assertEqual(normalize_domain('https://www.Example.com/contact'),'example.com')
 def test_dedupe(self):
  with tempfile.TemporaryDirectory() as d:
   db=db_open(d+'/db.sqlite');self.assertEqual(import_domains(db,['example.com','https://www.example.com']),1)
 def test_price(self):
  r=extract_prices('Guest post price is $75. We allow 2 do-follow links.');self.assertEqual(r['standard_price'],75);self.assertEqual(r['links'],2)
 def test_ambiguous(self): self.assertTrue(extract_prices('General $75, crypto $130')['needs_review'])
if __name__=='__main__':unittest.main()

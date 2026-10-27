"""Synthetic data only; no API key or real product identity is embedded."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from tools import private_source_export as e

class Client:
    def __init__(self):
        self.index={'property_id':e.PROPERTY,'products':[{'namespace':'catalogue','local_slug':'fixture'}]}
        self.value={'property_id':e.PROPERTY,'product_id':'prd_'+uuid4().hex,
            'identity':{'namespace':'catalogue','local_slug':'fixture'},'offers':[]}
        self.calls=0
        self.changed=False
    def get(self,path):
        if path.endswith('/offers?locale=nb'):
            return copy.deepcopy(self.value)
        self.calls+=1
        value=copy.deepcopy(self.index)
        if self.changed and self.calls>1:
            value['products']=[]
        return value

class ExportTests(unittest.TestCase):
    def test_native_property_binding_and_no_authority(self):
        c=Client();r=e.capture(c)
        self.assertEqual(r['products'][0],c.value)
        self.assertFalse(r['publication_authority'])
        self.assertEqual(r['evidence_mode'],'frozen_authorized_observation')
        self.assertEqual(c.calls,2)
    def test_held_identity_never_enters_export(self):
        c=Client()
        with patch.object(e,'EXCLUDED',{e.digest(c.value['product_id'].encode())}):
            r=e.capture(c)
        self.assertEqual(r['products'],[])
        self.assertEqual(r['catalogue']['products'],[])
        self.assertEqual(r['held_count'],1)
    def test_cross_property_and_wrong_alias_refused(self):
        for field in ('property_id','local_slug'):
            c=Client()
            if field=='property_id':c.value[field]='another-property'
            else:c.value['identity'][field]='another-alias'
            with self.assertRaises(e.Refused):e.capture(c)
    def test_changed_source_refused_without_retry(self):
        c=Client();c.changed=True
        with self.assertRaises(e.Refused):e.capture(c)
        self.assertEqual(c.calls,2)
    def test_duplicate_and_unsafe_alias_refused(self):
        c=Client();c.index['products']*=2
        with self.assertRaises(e.Refused):e.capture(c)
        c=Client();c.index['products'][0]['local_slug']='../another'
        with self.assertRaises(e.Refused):e.capture(c)
    def test_source_key_leak_refused_before_encryption(self):
        key=str(uuid4())
        with patch.object(e.subprocess,'run') as process:
            with self.assertRaises(e.Refused):e.encrypted_bytes({'bad':key},key,'age1fixture')
            process.assert_not_called()
    def test_key_never_passed_to_encryption_process(self):
        key=str(uuid4());doc={'synthetic':True}
        with patch.object(e.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'age-encryption.org/v1\nfixture')) as process:
            e.encrypted_bytes(doc,key,'age1fixture')
        self.assertNotIn(key,str(process.call_args))
        self.assertEqual(process.call_args.kwargs['input'],e.encode(doc))
    def test_budget_refused(self):
        c=Client();c.index['products']*=e.MAX_ROWS+1
        with self.assertRaises(e.Refused):e.capture(c)

if __name__=='__main__':unittest.main()

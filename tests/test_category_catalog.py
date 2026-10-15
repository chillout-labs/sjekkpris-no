import copy
import tempfile
import unittest
from pathlib import Path
from category_catalog import category_index, category_links, category_navigation
from home_release import write_home

class Categories(unittest.TestCase):
    def product(self):
        return {'namespace':'catalogue','local_slug':'one','local_name':'Produkt','categories':{'primary':{'id':'leaf','display_name':'Kjøkken','path':[{'id':'root','display_name':'Hjem'},{'id':'leaf','display_name':'Kjøkken'}]}}}

    def test_supplied_ancestors_and_duplicate_memberships(self):
        p=self.product();p['categories']['additional']=[copy.deepcopy(p['categories']['primary'])]
        nodes=category_index([p])
        self.assertEqual(list(nodes),['root','leaf'])
        self.assertEqual(len(nodes['root']['products']),1)
        self.assertEqual(nodes['root']['children'],['leaf'])
        self.assertEqual(category_links(p,nodes,'/beta/'),[('Hjem','/beta/kategori/hjem/'),('Kjøkken','/beta/kategori/kjokken/')])

    def test_missing_and_inactive_are_not_classified(self):
        p=self.product();p['categories']['primary']['active']=False
        self.assertEqual(category_index([p,{'local_category':'Invented'}]),{})

    def test_collisions_fail_instead_of_merging_categories(self):
        a=self.product();b=copy.deepcopy(a);b['categories']['primary']['id']='other';b['categories']['primary']['path']=[]
        with self.assertRaisesRegex(ValueError,'collision'):category_index([a,b])

    def test_builds_linked_preview_pages(self):
        p=self.product();nodes=category_index([p])
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            write_home([p],out,base='/beta/',noindex=True,day=lambda x:None,segment=str,categories=nodes)
            html=(out/'kategori/kjokken/index.html').read_text()
            self.assertIn('/beta/p/catalogue/one/',html)
            self.assertIn('/beta/kategori/hjem/',html)
            self.assertIn('content="noindex"',html)
            self.assertNotIn('data-category-id',html)
            self.assertTrue((out/'kategori/index.html').exists())
            self.assertIn('Alle kategorier',category_navigation(nodes,'/beta/'))

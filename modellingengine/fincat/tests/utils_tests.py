__author__ = 'Louise'

import xml.etree.ElementTree as ET

from nose.tools import eq_

from FinCat.utils import Parameters, ParameterDefinitions
import FinCat.utils as bnUtils


class TestParams:
    def setup(self):
        self.pDefs = ParameterDefinitions()
        self.pDefs.add_definition('test1', str, ["1", "2", "3", "doodah"])
        self.pDefs.add_definition('test2', int, [1, 3])
        self.pDefs.add_definition('test3', float, [2, 4])
        self.pDefs.add_definition('test4', str, ["4.1", "5.2", "6.3"])
        self.pDefs.add_definition('test5', int, [1, 2, 3, 4, 5])
        self.pDefs.add_definition('test6', float, [6.0, 6.1, 6.2, 6.3])
        self.pDefs.add_definition('test7', str)
        self.pDefs.add_definition('test8', int)
        self.pDefs.add_definition('test9', float)
        self.pDefs.add_definition('test10', int)
        self.pDefs.add_definition('test11', 'bool')
        self.pDefs.add_definition('test12', 'bool')
        self.xmlString = ("<parameters name='test1'>" +
                          "<simulator>" +
                          "<parameter name='assetSalesFactor' value='1.0' />" +
                          "<parameter name='randomSeed' value='12343' />" +
                          "<parameter name='balanceSheetMethod' value='externalAssetRatio' />" +
                          "</simulator>" +
                          "<economy name='econ1'>" +
                          "<parameter name='fireSaleFactor' value='0.0' />" +
                          "<parameter name='investmentCount' value='5' />" +
                          "<parameter name='externalAssetRatio' value='30' />" +
                          "<parameter name='capitalRatio' value='.15' />" +
                          "<parameter name='financialLiabilityRatio' value='.7' />" +
                          "</economy>" +
                          "<economy name='econ2'>" +
                          "<parameter name='fireSaleFactor' value='0.5' />" +
                          "<parameter name='investmentCount' value='10' />" +
                          "<parameter name='cashRatio' value='.15' />" +
                          "<parameter name='externalAssetRatio' value='40' />" +
                          "<parameter name='capitalRatio' value='0.2' />" +
                          "<parameter name='financialLiabilityRatio' value='.7' />" +
                          "</economy>" +
                          "<bank name='bank1' economy='econ1'>" +
                          "<parameter name='loanSize' value='10' />" +
                          "<parameter name='loanSD' value='2' />" +
                          "<parameter name='cashRatio' value='.1' />" +
                          "</bank>" +
                          "<bank name='bank2' economy='econ2'>" +
                          "<parameter name='loanSize' value='20' />" +
                          "<parameter name='loanSD' value='2' />" +
                          "<parameter name='financialLiabilityRatio' value='.2' />" +
                          "</bank>" +
                          "<bank name='bank3' economy='econ2'>" +
                          "<parameter name='loanSize' value='30' />" +
                          "<parameter name='loanSD' value='3' />" +
                          "<parameter name='externalAssetRatio' value='25' />" +
                          "<parameter name='capitalRatio' value='.125' />" +
                          "</bank>" +
                          "</parameters>")

    def test_params(self):
        set1 = Parameters(self.pDefs)
        set2 = Parameters(self.pDefs, set1)  # set2 uses set1 if it hasn't got values itself

        set1.set('test1', 1)  # should go in as a string
        set1.set('test2', 2)  # .. as an integer
        set1.set('test3', 3)  # and a float
        set1.set('test4', 4.1)  # should go in as a string
        set1.set('test5', 5.1)  # .. as an integer
        set1.set('test6', 6.1)  # and a float
        set1.set('test7', "7.1")  # should go in as a string
        set1.set('test8', "8")  # .. as an integer
        set1.set('test9', "9.1")  # and a float
        set1.set('test11', "true")
        set1.set('test12', "0")

        self.check_param(set1, 'test1', "1", str, 'set1')
        self.check_param(set1, 'test2', 2, int, 'set1')
        self.check_param(set1, 'test3', 3.0, float, 'set1')
        self.check_param(set1, 'test4', "4.1", str, 'set1')
        self.check_param(set1, 'test5', 5, int, 'set1')
        self.check_param(set1, 'test6', 6.1, float, 'set1')
        self.check_param(set1, 'test7', "7.1", str, 'set1')
        self.check_param(set1, 'test8', 8, int, 'set1')
        self.check_param(set1, 'test9', 9.1, float, 'set1')
        self.check_param(set1, 'test11', True, 'bool', 'set1')
        self.check_param(set1, 'test12', False, 'bool', 'set1')

        # no parameters have been set in set2 yet. So these should all come from set1.
        self.check_param(set2, 'test1', "1", str, 'set2')
        self.check_param(set2, 'test2', 2, int, 'set2')
        self.check_param(set2, 'test3', 3.0, float, 'set2')
        self.check_param(set2, 'test4', "4.1", str, 'set2')
        self.check_param(set2, 'test5', 5, int, 'set2')
        self.check_param(set2, 'test6', 6.1, float, 'set2')
        self.check_param(set2, 'test7', "7.1", str, 'set2')
        self.check_param(set2, 'test8', 8, int, 'set2')
        self.check_param(set2, 'test9', 9.1, float, 'set2')
        self.check_param(set2, 'test11', True, 'bool', 'set1')
        self.check_param(set2, 'test12', False, 'bool', 'set1')

        set2.set('test7', "27.1")  # should go in as a string
        set2.set('test8', "28")  # .. as an integer
        set2.set('test9', "29.1")  # and a float
        self.check_param(set2, 'test7', "27.1", str, 'set2')
        self.check_param(set2, 'test8', 28, int, 'set2')
        self.check_param(set2, 'test9', 29.1, float, 'set2')
        # the values in set1 haven't changed.
        self.check_param(set1, 'test7', "7.1", str, 'set1')
        self.check_param(set1, 'test8', 8, int, 'set1')
        self.check_param(set1, 'test9', 9.1, float, 'set1')

        v = set1.get("test10")   # doesn't exist
        assert v is None, "expected test10 not to exist in set1 but was %r" % v
        v = set1.get("test10", default=23)
        eq_(v, 23, "expected test10 to be 23, but is %r" % v)
        v = set2.get('test1', "gotcha")  # but it's in set1
        eq_(v, "1", "expected test1 to be %r, but is %r" % ("1", v))

    def test_xml(self):
        root = ET.fromstring(self.xmlString)

        simParams = root.find('simulator')
        sList = bnUtils.get_params_from_xml('simulator', 'simulator', simParams)
        eq_(len(sList), 3, "expected 3 simulator tuples but got %r" % len(sList))
        eList = bnUtils.get_entity_params_from_xml('economy', root, "test")
        eq_(len(eList), 13, "expected 13 economy tuples but got %r" % len(eList))
        bList = bnUtils.get_entity_params_from_xml('bank', root, 'test')
        eq_(len(bList), 16, "expected 16 bank tuples but got %r" % len(bList))
        pList = bnUtils.read_params_from_xml(root, 'test')
        eq_(len(pList), 32, "expected 32 total tuples but got %r" % len(pList))

        ans = bnUtils.get_value_from_pList(pList, 'bank', 'bank3', 'parameter', 'loanSize')
        eq_(ans, '30', "expected bank3 to have parameter loanSize of 30 but got %r" % ans)
        ans = bnUtils.get_value_from_pList(pList, 'economy', 'econ1', 'attribute', 'name')
        eq_(ans, 'econ1', "expected econ 1 to have attribute name of econ1 but got %r" % ans)

    def check_param(self, params, pName, val, pType, tag):
        if pName in params.params:
            v = params.params[pName]
            if pType == 'bool':
                assert v in [True, False], "expected %s in %s to be a boolean but is %r (1)" % (pName, tag, v)
            else:
                assert isinstance(v, pType), "expected %s's value in %s to be a %r but got %r (1)" % (
                    pName, tag, pType, type(v))
            eq_(v, val, "expected %s to be %r in %s but got %r (1)" % (pName, val, tag, v))
        v = params.get(pName)
        if pType == 'bool':
            assert v in [True, False], "expected %s in %s to be a boolean but is %r (2)" % (pName, tag, v)
        else:
            assert isinstance(v, pType), "expected %s's value in %s to be a %r but got %r (2)" % (
                pName, tag, pType, type(v))
        eq_(v, val, "expected %s to be %r in %s but got %r (2)" % (pName, val, tag, v))

# Testing of the PyCif module using the PyUnit framework
# 
import sys
sys.path[0] = '.'
print sys.path
import unittest, CifFile
import StarFile
import re

# Test basic setting and reading of the CifBlock

class BlockRWTestCase(unittest.TestCase):
    def setUp(self):
    	# we want to get a datablock ready so that the test
	# case will be able to write a single item
	self.cf = CifFile.CifBlock()

    def tearDown(self):
        # get rid of our test object
	del self.cf
	
    def testTupleNumberSet(self):
        """Test tuple setting with numbers"""
        self.cf['_test_tuple'] = (11,13.5,-5.6)
        self.failUnless(map(float,
	     self.cf['_test_tuple']))== [11,13.5,-5.6]

    def testTupleComplexSet(self):
        """Test setting multiple names in loop"""
	names = (('_item_name_1','_item_name#2','_item_%$#3'),)
	values = (((1,2,3,4),('hello','good_bye','a space','# 4'),
	          (15.462, -99.34,10804,0.0001)),)
        self.cf.AddCifItem((names,values))
	self.failUnless(tuple(map(float, self.cf[names[0][0]])) == values[0][0])
	self.failUnless(tuple(self.cf[names[0][1]]) == values[0][1])
	self.failUnless(tuple(map(float, self.cf[names[0][2]])) == values[0][2])

    def testStringSet(self):
        """test string setting"""
        self.cf['_test_string_'] = 'A short string'
	self.failUnless(self.cf['_test_string_'] == 'A short string')

    def testTooLongSet(self):
        """test setting overlong data names"""
        dataname = '_a_long_long_'*7
        try:
            self.cf[dataname] = 1.0
        except (StarFile.StarError,CifFile.CifError): pass
        else: self.fail()

    def testTooLongLoopSet(self):
        """test setting overlong data names in a loop"""
        dataname = '_a_long_long_'*7
        try:
            self.cf[dataname] = (1.0,2.0,3.0)
        except (StarFile.StarError,CifFile.CifError): pass
        else: self.fail()

    def testBadStringSet(self):
        """test setting values with bad characters"""
        dataname = '_name_is_ok'
        try:
            self.cf[dataname] = "eca234\f\vaqkadlf"
        except StarFile.StarError: pass
        else: self.fail()

    def testBadNameSet(self):
        """test setting names with bad characters"""
        dataname = "_this_is_not ok"
        try:
            self.cf[dataname] = "nnn"
        except StarFile.StarError: pass
        else: self.fail()

    def testMoreBadStrings(self):
        dataname = "_name_is_ok"
        val = u"so far, ok, but now we have a " + unichr(128)
        try:
            self.cf[dataname] = val
        except StarFile.StarError: pass
        else: self.fail()

    def testEmptyString(self):
        """An empty string is, in fact, legal"""
        self.cf['_an_empty_string'] = ''
        
    def testStarList(self):
        """Test that a StarList is treated as a primitive item"""
        self.cf['_a_star_list'] = StarFile.StarList([1,2,3,4])
        jj = self.cf.GetLoop('_a_star_list')
        self.failUnless(jj.dimension==0)
       
# Now test operations which require a preexisting block
#

class BlockChangeTestCase(unittest.TestCase):
   def setUp(self):
        self.cf = CifFile.CifBlock()
	self.names = (('_item_name_1','_item_name#2','_item_%$#3'),)
	self.values = (((1,2,3,4),('hello','good_bye','a space','# 4'),
	          (15.462, -99.34,10804,0.0001)),)
        self.cf.AddCifItem((self.names,self.values))
	self.cf['_non_loop_item'] = 'Non loop string item'
	self.cf['_number_item'] = 15.65
        self.cf['_planet'] = 'Saturn'
        self.cf['_satellite'] = 'Titan'
        self.cf['_rings']  = 'True'
       
   def tearDown(self):
       del self.cf

   def testFromBlockSet(self):
        """Test that we can use a CifBlock to set a CifBlock"""
        df = CifFile.CifFile()
        df.NewBlock('testname',self.cf)

   def testLoop(self):
        """Check GetLoop returns values and names in matching order"""
   	results = self.cf.GetLoop(self.names[0][2])
	for key in results.keys():
	    self.failUnless(key in self.names[0])
	    self.failUnless(tuple(results[key]) == self.values[0][list(self.names[0]).index(key)])
	
   def testSimpleRemove(self):
       """Check item deletion outside loop"""
       self.cf.RemoveCifItem('_non_loop_item')
       try:
           a = self.cf['_non_loop_item']
       except KeyError: pass
       else: self.fail()

   def testLoopRemove(self):
       """Check item deletion inside loop"""
       print "Before:\n"
       print self.cf.printsection()
       self.cf.RemoveCifItem(self.names[0][1])
       print "After:\n"
       print self.cf.printsection()
       try:
           a = self.cf[self.names[0][1]]
       except KeyError: pass
       else: self.fail()

   def testFullLoopRemove(self):
       """Check removal of all loop items"""
       for name in self.names[0]: self.cf.RemoveCifItem(name)
       self.failUnless(len(self.cf.loops)==0, `self.cf.loops`)

# test adding data to a loop.  We test straight addition, then make sure the errors
# happen at the right time
#
   def testAddToLoop(self):
       """Test adding to a loop"""
       adddict = {'_address':['1 high street','2 high street','3 high street','4 high st'],
                  '_address2':['Ecuador','Bolivia','Colombia','Mehico']}
       self.cf.AddToLoop('_item_name#2',adddict)
       newkeys = self.cf.GetLoop('_item_name#2').keys()
       self.failUnless(adddict.keys()[0] in newkeys)
       self.failUnless(len(self.cf.GetLoop('_item_name#2'))==len(self.values[0])+2)
       
   def testBadAddToLoop(self):
       """Test incorrect loop addition"""
       adddict = {'_address':['1 high street','2 high street','3 high street'],
                  '_address2':['Ecuador','Bolivia','Colombia']}
       try:
           self.cf.AddToLoop('_no_item',adddict)
       except KeyError: pass
       else: self.fail()
       try:
           self.cf.AddToLoop('_item_name#2',adddict)
       except StarFile.StarLengthError:
           pass 
       else: self.fail()

   def testChangeLoop(self):
       """Test changing pre-existing item in loop"""
       # Items should be silently replaced, but if an
       # item exists in a loop already, it should be
       # deleted from that loop first
       self.cf["_item_name_1"] = (5,6,7,8)

   def testLoopify(self):
       """Test changing unlooped data to looped data"""
       self.cf.Loopify(["_planet","_satellite","_rings"])
       newloop = self.cf.GetLoop("_rings")
       self.assertFalse(newloop.has_key("_number_item"))
       
   def testLoopifyCif(self):
       """Test changing unlooped data to looped data does 
          not touch already looped data for a CIF file"""
#      from IPython.Debugger import Tracer; debug_here = Tracer()
#      debug_here()
       self.cf.Loopify(["_planet","_satellite","_rings"])
       newloop = self.cf.GetLoop("_rings")
       newloop.Loopify(["_planet","_rings"])
       innerloop = newloop.GetLoop("_planet")
       self.assertTrue(innerloop.has_key("_satellite"))
       
#
#  Test the mapping type implementation
#
   def testGetOperation(self):
       """Test the get mapping call"""
       self.cf.get("_item_name_1")
       self.cf.get("_item_name_nonexist")

#
#  Test case insensitivity
#
   def testDataNameCase(self):
       """Test same name, different case causes error"""
       self.assertEqual(self.cf["_Item_Name_1"],self.cf["_item_name_1"])
       self.cf["_Item_NaMe_1"] = "the quick pewse fox"
       self.assertEqual(self.cf["_Item_NaMe_1"],self.cf["_item_name_1"])

#  Test iteration
#
   def testIteration(self):
       """We create an iterator and iterate"""
       testloop = self.cf.GetLoop("_item_name_1")
       i = 0
       for test_pack in testloop:
           self.assertEqual(test_pack._item_name_1,self.values[0][0][i]) 
           self.assertEqual(getattr(test_pack,"_item_name#2"),self.values[0][1][i]) 
           i += 1

   def testPacketContents(self):
       """Test that body of packet is filled in as well"""
       testloop = self.cf.GetLoop("_item_name_1")
       it_order = testloop.GetItemOrder()
       itn_pos = it_order.index("_item_name_1")
       for test_pack in testloop:
           print 'Test pack: ' + `test_pack`
           self.assertEqual(test_pack._item_name_1,test_pack[itn_pos])

   def testPacketAttr(self):
       """Test that packets have attributes"""
       testloop = self.cf.GetLoop("_item_name_1")
       self.assertEqual(testloop[1]._item_name_1,2)

   def testKeyPacket(self):
       """Test that a packet can be returned by key value"""
       testloop = self.cf.GetLoop("_item_name_1")
       testpack = testloop.GetKeyedPacket("_item_name_1",2)
       self.assertEqual("good_bye",getattr(testpack,"_item_name#2"))

   def testRemovePacket(self):
       """Test that removing a packet works properly"""
       print 'Before packet removal'
       print str(self.cf)
       testloop = self.cf.GetLoop("_item_name_1")
       testloop.RemoveKeyedPacket("_item_name_1",3)
       jj = testloop.GetKeyedPacket("_item_name_1",2)
       kk = testloop.GetKeyedPacket("_item_name_1",4)
       self.assertEqual(getattr(jj,"_item_name#2"),"good_bye")
       self.assertEqual(getattr(kk,"_item_name#2"),"# 4")
       self.assertRaises(KeyError,testloop.GetKeyedPacket,"_item_name_1",3)
       print 'After packet removal:'
       print str(self.cf)

   def testAddPacket(self):
       """Test that we can add a packet"""
       import copy
       testloop = self.cf.GetLoop("_item_name_1")
       workingpacket = copy.copy(testloop.GetPacket(0))
       workingpacket._item_name_1 = 5
       workingpacket.__setattr__("_item_name#2", 'new' )
       testloop.AddPacket(workingpacket)
       # note we assume that this adds on to the end, which is not 
       # a CIF requirement
       self.assertEqual(testloop["_item_name_1"][4],5)
       self.assertEqual(testloop["_item_name#2"][4],'new')

#
#  Test changing item order
#
   def testChangeOrder(self):
       """We move some stuff around"""
       testloop = self.cf.GetLoop("_item_name_1")
       self.cf.ChangeItemOrder("_Number_Item",0)
       testloop.ChangeItemOrder("_Item_Name_1",2)
       self.assertEqual(testloop.GetItemOrder()[2],"_Item_Name_1")
       self.assertEqual(self.cf.GetItemOrder()[0],"_Number_Item")
       
   def testGetOrder(self):
       """Test that the correct order value is returned"""
       self.assertEqual(self.cf.GetItemPosition("_Number_Item"),2)

   def testReplaceOrder(self):
       """Test that a replaced item is at the same position it
	  previously held"""
       testloop = self.cf.GetLoop("_item_name_1")
       oldpos = testloop.GetItemPosition('_item_name#2')
       testloop['_item_name#2'] = ("I'm",' a ','little','teapot')
       self.assertEqual(testloop.GetItemPosition('_item_name#2'),oldpos)
#
#  Test setting of block names
#

class BlockNameTestCase(unittest.TestCase):
   def testBlockName(self):
       """Make sure long block names cause errors"""
       df = CifFile.CifBlock()
       cf = CifFile.CifFile()
       try:
           cf['a_very_long_block_name_which_should_be_rejected_out_of_hand123456789012345678']=df
       except StarFile.StarError: pass
       else: self.fail()

   def testBlockOverwrite(self):
       """Upper/lower case should be seen as identical"""
       df = CifFile.CifBlock()
       ef = CifFile.CifBlock()
       cf = CifFile.CifFile(standard=None)
       df['_random_1'] = 'oldval'
       ef['_random_1'] = 'newval'
       print 'cf.standard is ' + `cf.standard`
       cf['_lowercaseblock'] = df
       cf['_LowerCaseBlock'] = ef
       assert(cf['_Lowercaseblock']['_random_1'] == 'newval')
       assert(len(cf) == 1)

   def testEmptyBlock(self):
       """Test that empty blocks are not the same object"""
       cf = CifFile.CifFile()
       cf.NewBlock('first_block')
       cf.NewBlock('second_block')
       cf['first_block']['_test1'] = 'abc'
       cf['second_block']['_test1'] = 'def'
       self.failUnless(cf['first_block']['_test1']=='abc')

#
#   Test reading cases
#
class FileWriteTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again. Non alphabetic ordering to
          check order preservation and mixed case."""
       # fill up the block with stuff
       items = (('_item_1','Some data'),
             ('_item_3','34.2332'),
             ('_item_4','Some very long data which we hope will overflow the single line and force printing of another line aaaaa bbbbbb cccccc dddddddd eeeeeeeee fffffffff hhhhhhhhh iiiiiiii jjjjjj'),
             ('_item_2','Some_underline_data'),
             ('_item_empty',''),
             ('_item_quote',"'ABC"),
             ('_item_apost','"def'),
             ('_item_sws'," \n "),
             (('_item_5','_item_7','_item_6'),
             ([1,2,3,4],
              ['a','b','c','d'],
              [5,6,7,8])),
             (('_string_1','_string_2'),
              ([';this string begins with a semicolon',
               'this string is way way too long and should overflow onto the next line eventually if I keep typing for long enough',
               ';just_any_old_semicolon-starting-string'],
               ['a string with a final quote"',
               'a string with a " and a safe\';',
               'a string with a final \''])))
       # save block items as well
       s_items = (('_sitem_1','Some save data'),
             ('_sitem_2','Some_underline_data'),
             ('_sitem_3','34.2332'),
             ('_sitem_4','Some very long data which we hope will overflow the single line and force printing of another line aaaaa bbbbbb cccccc dddddddd eeeeeeeee fffffffff hhhhhhhhh iiiiiiii jjjjjj'),
             (('_sitem_5','_sitem_6','_sitem_7'),
             ([1,2,3,4],
              [5,6,7,8],
              ['a','b','c','d'])),
             (('_string_1','_string_2'),
              ([';this string begins with a semicolon',
               'this string is way way too long and should overflow onto the next line eventually if I keep typing for long enough',
               ';just_any_old_semicolon-starting-string'],
               ['a string with a final quote"',
               'a string with a " and a safe\';',
               'a string with a final \''])))
       self.cf = CifFile.CifBlock(items)
       cif = CifFile.CifFile(scoping='dictionary')
       cif['Testblock'] = self.cf
       # Add some comments
       self.cf.AddComment('_item_empty',"Test of an empty string")
       self.cf.AddComment('_item_apost',"Test of a trailing apostrophe")
       self.save_block = CifFile.CifBlock(s_items)
       cif.NewBlock("test_Save_frame",self.save_block,parent='testblock')
       self.cfs = cif["test_save_frame"]
       outfile = open('test.cif','w')
       outfile.write(str(cif))
       outfile.close()
       self.ef = CifFile.CifFile('test.cif',scoping='dictionary')
       self.df = self.ef['testblock']
       self.dfs = self.ef["test_save_frame"]
       flfile = CifFile.ReadCif('test.cif',scantype="flex",scoping='dictionary')
       # test passing a stream directly
       tstream = open('test.cif')
       CifFile.CifFile(tstream,scantype="flex")
       self.flf = flfile['testblock']
       self.flfs = flfile["Test_save_frame"]

   def tearDown(self):
       import os
       #os.remove('test.cif')
       del self.dfs
       del self.df
       del self.cf
       del self.ef
       del self.flf
       del self.flfs

   def testStringInOut(self):
       """Test writing short strings in and out"""
       self.failUnless(self.cf['_item_1']==self.df['_item_1'])
       self.failUnless(self.cf['_item_2']==self.df['_item_2'])
       self.failUnless(self.cfs['_sitem_1']==self.dfs['_sitem_1'])
       self.failUnless(self.cfs['_sitem_2']==self.dfs['_sitem_2'])
       self.failUnless(self.cfs['_sitem_1']==self.flfs['_sitem_1'])
       self.failUnless(self.cfs['_sitem_2']==self.flfs['_sitem_2'])

   def testApostropheInOut(self):
       """Test correct behaviour for values starting with apostrophes
       or quotation marks"""
       self.failUnless(self.cf['_item_quote']==self.df['_item_quote'])
       self.failUnless(self.cf['_item_apost']==self.df['_item_apost'])
       self.failUnless(self.cf['_item_quote']==self.flf['_item_quote'])
       self.failUnless(self.cf['_item_apost']==self.flf['_item_apost'])
       
   def testNumberInOut(self):
       """Test writing number in and out"""
       self.failUnless(self.cf['_item_3']==(self.df['_item_3']))
       self.failUnless(self.cfs['_sitem_3']==(self.dfs['_sitem_3']))
       self.failUnless(self.cf['_item_3']==(self.flf['_item_3']))
       self.failUnless(self.cfs['_sitem_3']==(self.flfs['_sitem_3']))

   def testLongStringInOut(self):
       """Test writing long string in and out
          Note that whitespace may vary due to carriage returns,
	  so we remove all returns before comparing"""
       import re
       compstring = re.sub('\n','',self.df['_item_4'])
       self.failUnless(compstring == self.cf['_item_4'])
       compstring = re.sub('\n','',self.dfs['_sitem_4'])
       self.failUnless(compstring == self.cfs['_sitem_4'])
       compstring = re.sub('\n','',self.flf['_item_4'])
       self.failUnless(compstring == self.cf['_item_4'])
       compstring = re.sub('\n','',self.flfs['_sitem_4'])
       self.failUnless(compstring == self.cfs['_sitem_4'])

   def testEmptyStringInOut(self):
       """An empty string is in fact kosher""" 
       self.failUnless(self.cf['_item_empty']=='')
       self.failUnless(self.flf['_item_empty']=='')

   def testSemiWhiteSpace(self):
       """Test that white space in a semicolon string is preserved"""
       self.failUnless(self.cf['_item_sws']==self.df['_item_sws'])
       self.failUnless(self.cf['_item_sws']==self.flf['_item_sws'])

   def testLoopDataInOut(self):
       """Test writing in and out loop data"""
       olditems = self.cf.GetLoop('_item_5')
       for key,value in olditems.items():
           self.failUnless(tuple(map(str,value))==tuple(self.df[key]))
           self.failUnless(tuple(map(str,value))==tuple(self.flf[key]))
       # save frame test
       olditems = self.cfs.GetLoop('_sitem_5').items()
       for key,value in olditems:
           self.failUnless(tuple(map(str,value))==tuple(self.dfs[key]))
           self.failUnless(tuple(map(str,value))==tuple(self.flfs[key]))

   def testLoopStringInOut(self):
       """Test writing in and out string loop data"""
       olditems = self.cf.GetLoop('_string_1')
       newitems = self.df.GetLoop('_string_1')
       flexnewitems = self.flf.GetLoop('_string_1')
       for key,value in olditems.items():
           compstringa = map(lambda a:re.sub('\n','',a),value)
           compstringb = map(lambda a:re.sub('\n','',a),self.df[key])
           compstringc = map(lambda a:re.sub('\n','',a),self.flf[key])
           self.failUnless(compstringa==compstringb and compstringa==compstringc)

   def testGetLoopData(self):
       """Test the get method for looped data"""
       newvals = self.df.get('_string_1')
       self.failUnless(len(newvals)==3)

   def testCopySaveFrame(self):
       """Early implementations didn't copy the save frame properly"""
       jj = CifFile.CifFile(self.ef,scoping='dictionary')  #this will trigger a copy
       self.failUnless(len(jj["test_save_frame"])>0)

   def testFirstBlock(self):
       """Test that first_block returns a block"""
       self.ef.scoping = 'instance'  #otherwise all blocks are available
       jj = self.ef.first_block()
       self.failUnless(jj==self.df)

   def testDupName(self):
       """Test that duplicate blocknames are allowed in non-standard mode"""
       outstr = """data_block1 _data_1 b save_ab1 _data_2 c
                  save_
                  save_ab1 _data_3 d save_"""
       b = open("test2.cif","w")
       b.write(outstr)
       b.close()
       testin = CifFile.CifFile("test2.cif",standard=None)

##############################################################
#
#   Test alternative grammars (1.0, DDLm)
#
##############################################################
class GrammarTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again."""
       teststr1_0 = """
       #A test CIF file, grammar version 1.0 conformant
       data_Test
         _item_1 'A simple item'
         _item_2 '(Bracket always ok in quotes)'
         _item_3 (can_have_bracket_here_if_1.0)
       """
       f = open("test_1.0","w")
       f.write(teststr1_0)
       f.close()

   def tearDown(self):
	pass

   def testold(self):
       """Read in 1.0 conformant file; should not fail"""
       f = CifFile.ReadCif("test_1.0",grammar="1.0")  
       print f["test"]["_item_3"]
      
   def testNew(self):
       """Read in a 1.0 conformant file with 1.1 grammar; should fail"""
       try:
           f = CifFile.ReadCif("test_1.0",grammar="1.1")  
       except StarFile.StarError:
           pass

   def testObject(self):
       """Test use of grammar keyword when initialising object"""
       try:
           f = CifFile.CifFile("test_1.0",grammar="1.0")
       except StarFile.StarError:
           pass

class ParentChildTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a multi-save-frame file, read in again"""
       outstring = """
data_Toplevel
 _item_1         a
 save_1
   _s1_item1     b
   save_12
   _s12_item1    c
   save_
   save_13
   _s13_item1    d
   save_
 save_
 _item_2         e
 save_2
   _s2_item1     f
   save_21
   _s21_item1    g
     save_211
     _s211_item1 h
     save_
     save_212
     _s212_item1 i
     save_
    save_
   save_22
    _s22_item1   j
   save_
 save_
 save_toplevel
   _item_1       k
 save_
"""
       f = open('save_test.cif','w')
       f.write(outstring)
       f.close()
       self.testcif = CifFile.CifFile('save_test.cif',scoping='dictionary')

   def testGoodRead(self):
       """Check that there is a top level block"""
       self.failUnless('toplevel+' in [a[0] for a in self.testcif.child_table.items() if a[1].parent is None])
       self.failUnless(self.testcif.child_table['toplevel'].parent == 'toplevel+')

   def testGetParent(self):
       """Check that parent is correctly identified"""
       self.failUnless(self.testcif.get_parent('212')=='21')
       self.failUnless(self.testcif.get_parent('12')=='1')

   def testGetChildren(self):
       """Test that our child blocks are constructed correctly"""
       p = self.testcif.get_children('1')
       self.failUnless(p.has_key('13'))
       self.failUnless(not p.has_key('1'))
       self.failUnless(p.get_parent('13')==None)
       self.failUnless(p['12']['_s12_item1']=='c')

   def testGetChildrenwithParent(self):
       """Test that the parent is included if necessary"""
       p = self.testcif.get_children('1',include_parent=True)
       self.failUnless(p.has_key('1')) 
       self.failUnless(p.get_parent('13')=='1')
  
   def testSetParent(self):
       """Test that the parent is correctly set"""
       self.testcif.set_parent('1','211')
       q = self.testcif.get_children('1')
       self.failUnless('211' in q.keys())

   def testChangeParent(self):
       """Test that a duplicated save frame is OK if the duplicate name is a data block"""
       self.failUnless('toplevel+' in self.testcif.keys())
       self.failUnless(self.testcif.get_parent('1')=='toplevel+')

   def testRename1(self):
       """Test that re-identifying a datablock works"""
       self.testcif._rekey('2','timey-wimey')
       self.failUnless(self.testcif.get_parent('21')=='timey-wimey')
       self.failUnless(self.testcif.has_key('timey-wimey'))
       self.failUnless(self.testcif['timey-wimey']['_s2_item1']=='f')
       print str(self.testcif)
 
   def testRename2(self):
       """Test that renamng a block works"""
       self.testcif.rename('2','Timey-wimey')
       self.failUnless(self.testcif.has_key('timey-wimey'))
       self.failUnless(self.testcif.child_table['timey-wimey'].block_id=='Timey-wimey')
   
   def testUnlock(self):
       """Test that unlocking will change overwrite flag"""
       self.testcif['2'].overwrite = False
       self.testcif.unlock()
       self.failUnless(self.testcif['2'].overwrite is True)

class DDLmTestCase(unittest.TestCase):
   def setUp(self):
       """Write out a file, then read it in again."""
       teststr1_2 = """
       #A test CIF file, grammar version 1.2 nonconformant
       data_Test
         _item_1 'A simple item'
         _item_2 '(Bracket always ok in quotes)'
         _item_3 (can_have_bracket_here_if_1.2)
         _item_4 This_is_so_wrong?*~
       """
       goodstr1_2 = """
       #A test CIF file, grammar version 1.2 conformant with nested save frames
       data_Test
          _name.category_id           CIF_DIC
          _name.object_id             CIF_CORE
          _import.get       
        [{"save":'EXPERIMENTAL', "file":'core_exptl.dic', "mode":'full' },
         {"save":'DIFFRACTION',  "file":'core_diffr.dic', "mode":'full' },
         {"save":'STRUCTURE',    "file":'core_struc.dic', "mode":'full' },
         {"save":'MODEL',        "file":'core_model.dic', "mode":'full' },
         {"save":'PUBLICATION',  "file":'core_publn.dic', "mode":'full' },
         {"save":'FUNCTION',     "file":'core_funct.dic', "mode":'full' }]
        save_Savelevel1
         _item_in_save [1,2,3,4]
         save_saveLevel2
            _item_in_inside_save {"hello":"goodbye","e":"mc2"}
         save_
        save_
         _test.1 {"piffle":poffle,"wiffle":3,'''woffle''':9.2}
         _test_2 {"ping":[1,2,3,4],"pong":[a,b,c,d]}
         _test_3 {"ppp":{'qqq':2,'poke':{'joke':[5,6,7],'jike':[{'aa':bb,'cc':dd},{'ee':ff,"gg":100}]}},"rrr":[11,12,13]}
         _triple_quote_test '''The comma is ok if, the quotes
                                are ok'''
         _underscore_test underscores_are_allowed_inside_text
       """
       f = open("test_1.2","w")
       f.write(teststr1_2)
       f.close()
       f = open("goodtest_1.2","w")
       f.write(goodstr1_2)
       f.close()

   def tearDown(self):
	pass

   def testold(self):
       """Read in 1.2 nonconformant file; should fail"""
       try:
           f = CifFile.ReadCif("test_1.2",grammar="DDLm")  
       except StarFile.StarError:
           pass
      
   def testgood(self):
       """Read in 1.2 conformant file: should succeed"""
       f = CifFile.ReadCif("goodtest_1.2",grammar="DDLm")
       
   def testTables(self):
       """Test that DDLm tables are properly parsed"""
       f = CifFile.ReadCif("goodtest_1.2",grammar="DDLm")
       self.failUnless(f["test"]["_test.1"]["wiffle"] == '3')

   def testTables2(self):
       """Test that a plain table is properly parsed"""
       f = CifFile.ReadCif("goodtest_1.2",grammar="DDLm")
       self.failUnless(f["test"]["_import.get"][0]["file"] == 'core_exptl.dic')

   def testTables3(self):
       """Test that a nested structure is properly parsed"""
       f = CifFile.ReadCif("goodtest_1.2",grammar="DDLm")
       self.failUnless(f["test"]["_test_3"]["ppp"]["poke"]["jike"][1]["gg"]=='100')

   def testTripleQuote(self):
       """Test that triple quoted values are treated correctly"""
       f = CifFile.ReadCif("goodtest_1.2",grammar="DDLm")
       print f["test"]["_triple_quote_test"]
       self.failUnless(f["test"]["_triple_quote_test"][:9] == 'The comma')

##########
#
# Test DDLm imports
#
##########
class DDLmImportCase(unittest.TestCase):
    def setUp(self):
        pass

##############################################################
#
# Test dictionary type
#
##############################################################
ddl1dic = CifFile.CifDic("dictionaries/cif_core.dic")

class DictTestCase(unittest.TestCase):
    def setUp(self):
	self.ddldic = CifFile.CifDic("tests/ddl.dic",grammar='DDLm',scoping='dictionary')  #small DDLm dictionary
    
    def tearDown(self):
	pass

    def testnum_and_esd(self):
        """Test conversion of numbers with esds"""
        testnums = ["5.65","-76.24(3)","8(2)","6.24(3)e3","55.2(2)d4"]
        res = map(CifFile.get_number_with_esd,testnums)
        print `res`
        self.failUnless(res[0]==(5.65,None))
        self.failUnless(res[1]==(-76.24,0.03))
        self.failUnless(res[2]==(8,2))
        self.failUnless(res[3]==(6240,30))
        self.failUnless(res[4]==(552000,2000))
         
    def testdot(self):
        """Make sure a single dot is skipped"""
        res1,res2 = CifFile.get_number_with_esd(".")
        self.failUnless(res1==None)

    def testCategoryRename(self):
        """Test that renaming a category works correctly"""
        self.ddldic.change_category_name('Description','Opisanie')
        self.failUnless(self.ddldic.has_key('opisanie'))
        self.failUnless(self.ddldic['opisanie']['_name.object_id']=='Opisanie')
        self.failUnless(self.ddldic.has_key('opisanie.text'))
        self.failUnless(self.ddldic['opisanie.text']['_name.category_id']=='Opisanie')
        self.failUnless(self.ddldic['opisanie.text']['_definition.id']=='_Opisanie.text')
        self.failUnless(self.ddldic.has_key('description_example'))

    def testChangeItemCategory(self):
        """Test that changing an item's category works"""
        self.ddldic.change_category('_description.common','type')
        self.failUnless('_type.common' in self.ddldic)
        self.failUnless('_description.common' not in self.ddldic)
        self.failUnless(self.ddldic['_type.common']['_name.category_id'].lower()=='type')

    def testChangeCategoryCategory(self):
        """Test that changing a category's category works"""
        self.ddldic.change_category('description_example','attributes')
        self.failUnless(self.ddldic['description_example']['_name.category_id'].lower()=='attributes')

    def testChangeName(self):
        """Test that changing the object_id works"""
        self.ddldic.change_name('_description.common','uncommon')
        self.failUnless('_description.uncommon' in self.ddldic)
        self.failUnless('_description.common' not in self.ddldic)
        self.failUnless(self.ddldic['_description.uncommon']['_name.object_id']=='uncommon')
        self.failUnless(self.ddldic['_description.uncommon']['_definition.id']=='_description.uncommon')

    def testNewCategory(self):
        """Test that we can add a new category"""
        self.ddldic.add_category('brand-new')
        self.failUnless('brand-new' in self.ddldic)
        self.failUnless(self.ddldic['brand-new']['_name.object_id']=='brand-new')
        self.failUnless(self.ddldic.get_parent('brand-new').lower()=='attributes')
        self.failUnless(self.ddldic['brand-new']['_name.category_id'].lower()=='attributes')

    def testNewDefinition(self):
        """Test that we can add a new definition"""
        self.ddldic.add_definition('_junkety._junkjunk_','description')
        self.failUnless('_description.junkjunk' in self.ddldic)
        self.failUnless(self.ddldic['_description.junkjunk']['_name.category_id'].lower()=='description')
        self.failUnless(self.ddldic['_description.junkjunk']['_name.object_id']=='junkjunk')
        self.failUnless(self.ddldic['_description.junkjunk']['_definition.id']=='_description.junkjunk')

##############################################################
#
#  Validation testing
#
##############################################################

# We first test single item checking
class DDL1TestCase(unittest.TestCase):

    def setUp(self):
	# self.ddl1dic = CifFile.CifFile("dictionaries/cif_core.dic")
	#items = (("_atom_site_label","S1"),
	#	 ("_atom_site_fract_x","0.74799(9)"),
        #         ("_atom_site_adp_type","Umpe"),
	#	 ("_this_is_not_in_dict","not here"))
	bl = CifFile.CifBlock()
	self.cf = CifFile.ValidCifFile(dic=ddl1dic)
	self.cf["test_block"] = bl
	self.cf["test_block"].AddCifItem(("_atom_site_label",
	      ["C1","Cr2","H3","U4"]))	

    def tearDown(self):
        del self.cf

    def testItemType(self):
        """Test that types are correctly checked and reported"""
        #numbers
        self.cf["test_block"]["_diffrn_radiation_wavelength"] = "0.75"
        try:
            self.cf["test_block"]["_diffrn_radiation_wavelength"] = "moly"
        except CifFile.ValidCifError: pass

    def testItemEsd(self):
        """Test that non-esd items are not allowed with esds"""
        #numbers
        try:
            self.cf["test_block"]["_chemical_melting_point_gt"] = "1325(6)"
        except CifFile.ValidCifError: pass

    def testItemEnum(self):
        """Test that enumerations are understood"""
        self.cf["test_block"]["_diffrn_source_target"]="Cr"
        try:
            self.cf["test_block"]["_diffrn_source_target"]="2.5"
        except CifFile.ValidCifError: pass 
        else: self.fail()

    def testItemRange(self):
        """Test that ranges are correctly handled"""
        self.cf["test_block"]["_diffrn_source_power"] = "0.0"
        self.cf["test_block"]["_diffrn_standards_decay_%"] = "98"

    def testItemLooping(self):
        """test that list yes/no/both works"""
        pass

    def testListReference(self):
        """Test that _list_reference is handled correctly"""
        #can be both looped and unlooped; if unlooped, no need for ref.
        self.cf["test_block"]["_diffrn_radiation_wavelength"] = "0.75"
        try:
            self.cf["test_block"].AddCifItem(((
                "_diffrn_radiation_wavelength",
                "_diffrn_radiation_wavelength_wt"),(("0.75","0.71"),("0.5","0.1"))))
        except CifFile.ValidCifError: pass
        else: self.fail()
        
    def testUniqueness(self):
        """Test that non-unique values are found"""
        # in cif_core.dic only one set is available
        try:
            self.cf["test_block"].AddCifItem(((
                "_publ_body_label",
                "_publ_body_element"),
                  (
                   ("1.1","1.2","1.3","1.2"),
                   ("section","section","section","section") 
                     )))
        except CifFile.ValidCifError: pass
        else: self.fail()

    def testParentChild(self):
	"""Test that non-matching values are reported"""
        self.assertRaises(CifFile.ValidCifError,
	    self.cf["test_block"].AddCifItem,
	    (("_geom_bond_atom_site_label_1","_geom_bond_atom_site_label_2"),
	      [["C1","C2","H3","U4"],
	      ["C1","Cr2","H3","U4"]]))	
	# now we test that a missing parent is flagged
        # self.assertRaises(CifFile.ValidCifError,
	#     self.cf["test_block"].AddCifItem,
	#     (("_atom_site_type_symbol","_atom_site_label"),
	#       [["C","C","N"],["C1","C2","N1"]]))

    def testReport(self):
        CifFile.validate_report(CifFile.validate("tests/C13H2203_with_errors.cif",dic=ddl1dic))

class FakeDicTestCase(unittest.TestCase):
# we test stuff that hasn't been used in official dictionaries to date.
    def setUp(self):
        self.testcif = CifFile.CifFile("dictionaries/novel_test.cif")

    def testTypeConstruct(self):
        self.assertRaises(CifFile.ValidCifError,CifFile.ValidCifFile,
                           diclist=["dictionaries/novel.dic"],datasource=self.testcif)
          
class DicMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.offdic = CifFile.CifFile("dictionaries/dict_official",standard=None)
        self.adic = CifFile.CifFile("dictionaries/dict_A",standard=None)
        self.bdic = CifFile.CifFile("dictionaries/dict_B",standard=None)
        self.cdic = CifFile.CifFile("dictionaries/dict_C",standard=None)
        self.cvdica = CifFile.CifFile("dictionaries/cvdica.dic",standard=None)
        self.cvdicb = CifFile.CifFile("dictionaries/cvdicb.dic",standard=None)
        self.cvdicc = CifFile.CifFile("dictionaries/cvdicc.dic",standard=None)
        self.cvdicd = CifFile.CifFile("dictionaries/cvdicd.dic",standard=None)
        self.testcif = CifFile.CifFile("dictionaries/merge_test.cif",standard=None)
       
    def testAStrict(self):
        self.assertRaises(StarFile.StarError,CifFile.merge_dic,[self.offdic,self.adic],mergemode="strict")
        
    def testAOverlay(self):
        newdic = CifFile.merge_dic([self.offdic,self.adic],mergemode='overlay')
        # print newdic.__str__()
        self.assertRaises(CifFile.ValidCifError,CifFile.ValidCifFile,
                                  datasource="dictionaries/merge_test.cif",
                                  dic=newdic)
        
#    def testAReverseO(self):
#        # the reverse should be OK!
#        newdic = CifFile.merge_dic([self.adic,self.offdic],mergemode='overlay')
#        jj = CifFile.ValidCifFile(datasource="dictionaries/merge_test.cif",
#                                 dic = newdic)

#    def testCOverlay(self):
#        self.offdic = CifFile.merge_dic([self.offdic,self.cdic],mergemode='replace') 
#        print "New dic..."
#        print self.offdic.__str__()
#        self.assertRaises(CifFile.ValidCifError,CifFile.ValidCifFile,
#                          datasource="dictionaries/merge_test.cif",
#                          dic = self.offdic)

    # now for the final example in "maintenance.html"
    def testCVOverlay(self):
        jj = open("merge_debug","w")
        newdic = CifFile.merge_dic([self.cvdica,self.cvdicb,self.cvdicc,self.cvdicd],mergemode='overlay')
        jj.write(newdic.__str__())

#    def testKeyOverlay(self):
#        """Test that duplicate key values are not overlayed in loops"""
#        ff = CifFile.CifFile("dictionaries/merge_test_2.cif")["block_a"]
#        gg = CifFile.CifFile("dictionaries/merge_test_2.cif")["block_b"]
#        ff.merge(gg,mode="overlay",rel_keys = ["_loop_key"])
#        target_loop = ff.GetLoop("_loop_key")
#        print ff.__str__()

    def tearDown(self):
        pass

if __name__=='__main__':
    unittest.main()


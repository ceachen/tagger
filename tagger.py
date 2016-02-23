'''
^ name: tag tool
^ author: tillfall(tillfall@126.com)
^ version: 0.1
^ create: 2016-02-24
^ platform: py2.7 & wx3.0
^ --------
'''

import wx
import wx.lib.inspection
import wx.lib.mixins.inspection
import  wx.gizmos   as  gizmos
import  wx.lib.mixins.listctrl  as  listmix
import  wx.html as  html
from wx.lib.embeddedimage import PyEmbeddedImage
import sys, os
import codecs
import unittest

#--------BEGIG default config
PATH_CONFIG_F_NAME = '_pathes.txt'
TAG_CONFIG_F_NAME = '_tags.htm'
ITEM_CONFIG_F_NAME = '_items.txt'

READONLY = 'ro'

#--------BEGIN ui utils
class ui_utils(object):
    _log_inited = False
    @staticmethod
    def _log_init():
        wx.Log.SetActiveTarget(wx.LogStderr())
        ui_utils._log_inited = True
    @staticmethod
    def log(text):
        if not ui_utils._log_inited:
            ui_utils._log_init()
        if text[-1:] == '\n':
            text = text[:-1]
        wx.LogMessage(text)
    @staticmethod
    def warn(text):
        ui_utils.log('[W]%s'%text)
    @staticmethod
    def error(text):
        ui_utils.log('[E]%s'%text)
        
    @staticmethod
    def get_UpArrow():
        return PyEmbeddedImage(
            "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAADxJ"
            "REFUOI1jZGRiZqAEMFGke2gY8P/f3/9kGwDTjM8QnAaga8JlCG3CAJdt2MQxDCAUaOjyjKMp"
            "cRAYAABS2CPsss3BWQAAAABJRU5ErkJggg==")
    @staticmethod
    def get_DnArrow():
        return PyEmbeddedImage(
            "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAEhJ"
            "REFUOI1jZGRiZqAEMFGke9QABgYGBgYWdIH///7+J6SJkYmZEacLkCUJacZqAD5DsInTLhDR"
            "bcPlKrwugGnCFy6Mo3mBAQChDgRlP4RC7wAAAABJRU5ErkJggg==")
            
    @staticmethod
    def addFullExpandChildComponent(parent, child):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(child, 1, wx.EXPAND)
        parent.SetSizer(sizer)
        parent.SetAutoLayout(True)
        
        child.SetSize(parent.GetSize())
        child.SetBackgroundColour(parent.GetBackgroundColour())
        
class MainWin(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)
    def OnInit(self):
        frame = wx.Frame(None, -1, "tagger", pos=(50,50), size=(800,600),
                        style=wx.DEFAULT_FRAME_STYLE, name="tagger")
        frame.CreateToolBar()
        frame.CreateStatusBar()
        
        frame.Show(True)
        frame.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        self.SetTopWindow(frame)
        self.frame = frame
        return True
    def OnExitApp(self, evt):
        self.frame.Close(True)
    def OnCloseFrame(self, evt):
        if hasattr(self, "window") and hasattr(self.window, "ShutdownDemo"):
            self.window.ShutdownDemo()
        evt.Skip()
    def show(self):
        self.MainLoop()
        
    def getViewPort(self):
        return self.frame
    #def setMainView(self, mainView):
    #    #self.mainView = mainView
    #    ui_utils.addFullExpandChildComponent(self.getViewPort(), mainView)
        
class HtmlView(html.HtmlWindow):
    def __init__(self, parent, evtHandler):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        ui_utils.addFullExpandChildComponent(parent, self)
        self.evtHandler = evtHandler
    def OnCellClicked(self, cell, x, y, evt):
        if isinstance(cell, html.HtmlWordCell):
            sel = html.HtmlSelection()
            self.evtHandler(cell.ConvertToText(sel))
        super(HtmlView, self).OnCellClicked(cell, x, y, evt)
    def refreshData(self, htmlStr):
        self.SetPage(htmlStr)
        
class SplitView(object):
    def __init__(self, parent, p1Color='Pink', p2Color='Aquamarine', p3Color='Light Blue', lWidth=200, tHeight=300, minSize=80):
        self.firstPanel = wx.SplitterWindow(parent, -1, style = wx.SP_LIVE_UPDATE)
        self.secondPanel = wx.SplitterWindow(self.firstPanel, -1, style = wx.SP_LIVE_UPDATE)
        
        sty = wx.NO_FULL_REPAINT_ON_RESIZE
        p1 = wx.Panel(self.secondPanel, -1, style=sty)
        p2 = wx.Panel(self.secondPanel, -1, style=sty)
        p3 = wx.Panel(self.firstPanel, -1, style=sty)
        p1.SetBackgroundColour(p1Color)
        p2.SetBackgroundColour(p2Color)        
        p3.SetBackgroundColour(p3Color)
        
        self.firstPanel.SplitVertically(self.secondPanel, p3, lWidth)
        self.secondPanel.SplitHorizontally(p1, p2, tHeight)
        self.firstPanel.SetMinimumPaneSize(minSize)
        self.secondPanel.SetMinimumPaneSize(minSize)

        self.mainView = self.firstPanel
        self.p1, self.p2, self.p3 = p1, p2, p3
        
class ListView(wx.ListCtrl,
           listmix.ListCtrlAutoWidthMixin,
           listmix.TextEditMixin,
           listmix.ColumnSorterMixin):#for sort
    def __init__(self, parent, columns):
        wx.ListCtrl.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT
                                 | wx.BORDER_NONE
                                 | wx.LC_SORT_ASCENDING)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 100)
        
        #for sort
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(ui_utils.get_UpArrow().GetBitmap())
        self.sm_dn = self.il.Add(ui_utils.get_DnArrow().GetBitmap())
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        
        self.columns = columns
        self.initColumns()
        
        ui_utils.addFullExpandChildComponent(parent, self)
        
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)
        
    def initColumns(self):
        i = 0
        for col in self.columns:
            self.InsertColumn(i, col[0], col[2])
            self.SetColumnWidth(i, col[1])
            i += 1
    
    '''
    {1 : ("Bad English", "The Price Of Love", "Rock"),
    2 : ("DNA featuring Suzanne Vega", "Tom's Diner", "Rock"),
    3 : ("George Michael", "Praying For Time", "Rock"),}
    '''
    def refreshData(self, listItemDict):
        self.itemDataMap = listItemDict
        
        self.DeleteAllItems()
        for key, data in listItemDict.items():
            index = self.InsertStringItem(sys.maxint, data[0])
            for i in range(1, len(data)):
                self.SetStringItem(index, i, data[i])
            self.SetItemData(index, key)
                   
#--------BEGIN Model_Serializable
class io(object):
    @staticmethod
    def load(fname=PATH_CONFIG_F_NAME):
        lines = []
        if os.path.isfile(fname):
            file = codecs.open(fname, 'r', 'gb2312')
            lines = [x.strip() for x in file.readlines()]
            file.close()
            ui_utils.log('load %s, %d lines' % (fname, len(lines)))
        return lines
    @staticmethod
    def save(lst, fname=PATH_CONFIG_F_NAME):
        file = codecs.open(fname, 'w', 'gb2312')
        for l in lst:
            file.write('%s\n'%l)
        file.close()
        ui_utils.log('save %s, %d lines' % (fname, len(lst)))
               
#--------BEGIN Model
class Model(object):
    '''
    {1 : (path1, ), 2 : (path2, ), }
    '''
    def __init__(self):
        self.pathes = {}
        idx = 0
        for line in io.load(PATH_CONFIG_F_NAME):
            self.pathes[idx] = (line, )
            idx += 1
            
        self.tags = {}
        self.tagHtmlStr = '\n'.join(io.load(TAG_CONFIG_F_NAME))
        
        '''
        name;width;align;ro, path, create, tag1;tag2;tag3, comment...
        '''
        lines = io.load(ITEM_CONFIG_F_NAME)
        self.itemColumnStr = line[0]
        self.itemcolumns = self.setColumns(lines[0])
        self.itemdata = {}
        self.tag2item = {}
        self.initItems(lines[1:])
        
        print self.itemcolumns
        print ['%s:%d'%(t,len(i)) for t,i in self.tag2item.items()]
    
    def initItems(self, lines):
        idx = 0
        for line in lines:
            linestr = line.split(',')
            self.itemdata[idx] = linestr
            
            tagstr = linestr[-2]
            if len(tagstr) > 1:
                for aTag in tagstr.split(';'):
                    if aTag in self.tag2item.keys():
                        self.tag2item[aTag] += [linestr]
                    else:
                        self.tag2item[aTag] = [linestr]
            
            idx += 1
        
    def setColumns(self, colStr):
        columns = []
        for col in colStr.split(','):
            attrs = col.split(';')
            column = []
            column.append(attrs[0])
            column.append(int(attrs[1]))
            if 'left' in attrs[2].lower():
                column.append(wx.LIST_FORMAT_LEFT)
            else:
                column.append(wx.LIST_FORMAT_RIGHT)
            column.append(attrs[3])
            columns.append(column)
        return columns
        
    def getPathes(self):
        return self.pathes
    def _getIdByPath(self, aPath):
        for id in self.pathes.keys():
            if aPath == self.pathes[id][0]:
                return id
        return -1
    def addPath(self, newpath):
        id = self._getIdByPath(newpath)
        if not -1 == id:
            ui_utils.warn('%s already exists'%newpath)
            return id
        else:
            if {} == self.pathes:
                newid = 1
            else:
                newid = max(self.pathes.keys()) + 1
            self.pathes[newid] = (newpath, )
            ui_utils.log('model add %s, pathes count is %d'%(newpath,len(self.pathes.keys())))
            return newid
    def rmvPath(self, oldpath):
        id = self._getIdByPath(oldpath)
        if not -1 == id:
            self.pathes.pop(id)
            ui_utils.log('model rmv %s, pathes count is %d'%(oldpath,len(self.pathes.keys())))
            return True
        else:
            ui_utils.warn('%s not exists'%oldpath)
            return False

#--------BEGIN Controllor
class EventHandler(object):
    def __init__(self, sender, model, modelKeyColIdx=0):
        self.sender = sender
        self.model = model
        self.modelKeyColIdx = modelKeyColIdx
    def listBeginEdit(self, event):#disable edit: path, tags
        '''
        ^ edit grid cell, some column READONLY by 'ro'
        ^ --------
        '''
        if READONLY == self.sender.columns[event.Column][3]:
            event.Veto()#Readonly
        else:
            ui_utils.log('evt edit from %s' % event.Text)
    def listEndEdit(self, event):#edit
        ui_utils.log('evt edit to %s' % event.Text)
        event.Allow()
        
    def listKeyDown(self, event):
        '''
        ^ remove item by click DEL key, multi select is supported
        ^ --------
        '''
        if 127 == event.GetKeyCode():#delete
            list = self.sender
            selectedRow = list.GetFirstSelected()
            while not -1 == selectedRow:
                selKey = list.GetItem(selectedRow, self.modelKeyColIdx).GetText()
                self.model.rmvPath(selKey)
                ui_utils.log('evt rmv %s'%selKey)
                selectedRow = list.GetNextSelected(selectedRow)
            list.refreshData(self.model.getPathes())#TODO: refresh item
            
            self._savePathes()#TODO: save item
        
    def htmlTagClick(self, tagStr):#select tag
        '''
        ^ filter by click tag
        ^ --------
        '''
        ui_utils.log(tagStr)
        
    def onDropFile(self, x, y, filenames):#add path
        '''
        ^ drag&drop path to path list
        ^ insert path(es) to tag their sub dirs or files
        ^ --------
        '''
        for file in filenames:
            #ui_utils.log(file)
            self.model.addPath(file)
            self.sender.refreshData(self.model.getPathes())
            
        self._savePathes()
            
    def _savePathes(self):
        pathes = [p[0] for p in self.model.getPathes().values()]
        io.save(pathes, PATH_CONFIG_F_NAME)
            
class FileDropTarget(wx.FileDropTarget):
    def __init__(self, window, model):
        wx.FileDropTarget.__init__(self)  
        self.window = window
        window.SetDropTarget(self)
        self.dropFile = EventHandler(self.window, model).onDropFile
    def OnDropFiles(self, x, y, filenames):
        self.dropFile(x, y, filenames)            
#--------BEGIN UI
            
#--------BEGIN Test        
class test_ui(unittest.TestCase):
    def test_log(self):
        ui_utils.log('test log')
        ui_utils.log('test log again')
    def test_upanddn_ico(self):
        ui_utils.get_DnArrow()
        ui_utils.get_UpArrow()
    def test_sizer(self):
        app = wx.PySimpleApp()
        parent = wx.Frame(None, -1)
        child = wx.Panel(parent)
        ui_utils.addFullExpandChildComponent(parent, child)
        
class test_io(unittest.TestCase):
    def test_load_pathes(self):
        lines = io.load(PATH_CONFIG_F_NAME)
        self.assertTrue(len(lines)>1)
    def test_load_tags(self):
        lines = io.load(TAG_CONFIG_F_NAME)
        self.assertTrue(len(lines)>1)
class test_model(unittest.TestCase):
    def setUp(self):
        self.model = Model()
        self.pathes = self.model.getPathes()
    def test_load_pathes(self):
        self.assertTrue(len(self.pathes.keys())>1)
    def test_add_path(self):
        pathesCount = len(self.model.getPathes())
        self.model.addPath('jadfadsfmlk')
        self.assertTrue(len(self.model.getPathes()) == pathesCount + 1)
        self.model.addPath('jadfadsfmlk')
        self.assertTrue(len(self.model.getPathes()) == pathesCount + 1)
    def test_rmv_path(self):
        self.model.addPath('jadfadsfmlk')
        pathesCount = len(self.model.getPathes())
        self.model.rmvPath('jadfadsfmlk')
        self.assertTrue(len(self.model.getPathes()) == pathesCount - 1)
        self.model.rmvPath('jadfadsfmlk')
        self.assertTrue(len(self.model.getPathes()) == pathesCount - 1)
        
#unittest.TestProgram().runTests()
def testMainWin():
    mainWin = MainWin()
    model = Model()

    #panel = wx.Panel(mainWin.getViewPort(), -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
    #btn = wx.Button(panel, label = 'test', pos = (150, 60), size = (100, 60))
    #mainWin.setMainView(panel)
    
    view1 = SplitView(mainWin.getViewPort())
    #box = wx.BoxSizer(wx.VERTICAL)
    #box.Add(view1.mainView, 0, wx.EXPAND)
    
    view2 = HtmlView(view1.p1, EventHandler(None, model).htmlTagClick)
    #view2.refreshData(TAG_CONFIG_F_NAME)
    view2.refreshData(model.tagHtmlStr)
    
    view3 = ListView(view1.p2, (('Pathes', 200, wx.LIST_FORMAT_LEFT, 'ro'), ))
    evtHandler = EventHandler(view3, model)
    view3.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler.listBeginEdit)
    view3.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.listEndEdit)
    view3.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.listKeyDown)
    view3.refreshData(model.getPathes())
    FileDropTarget(view3, model)
    
    view4 = ListView(view1.p3, model.itemcolumns)
    evtHandler = EventHandler(view4, None)
    view4.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler.listBeginEdit)
    view4.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.listEndEdit)
    view4.refreshData(model.itemdata)
            
    mainWin.show()

if "__main__" == __name__:
    testMainWin()

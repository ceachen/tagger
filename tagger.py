'''
^ name: tag tool
^ author: tillfall(tillfall@126.com)
^ version: 1.0
^ create: 2016-02-21
^ release: 2016-02-25
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
import re
import unittest

#--------BEGIG default config
PATH_CONFIG_F_NAME = '_pathes.txt'
TAG_CONFIG_F_NAME = '_tags.htm'
ITEM_CONFIG_F_NAME = '_items.txt'

READONLY = 'ro'
SYS_TAG_NEW = 'sys-new'
SYS_TAG_DEL = 'sys-del'
ALL_TAG ='ALL'

TAG_COL_IDX = 3
PATH_COL_IDX = 1

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
        #frame.CreateToolBar()
        self.sb = frame.CreateStatusBar()
        
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
        
    def log(self, text):
        self.sb.PushStatusText(text)
        
    def getViewPort(self):
        return self.frame
        
class HtmlView(html.HtmlWindow):
    def __init__(self, parent, evtHandler):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.evtHandler = evtHandler
    def OnCellClicked(self, cell, x, y, evt):
        if isinstance(cell, html.HtmlWordCell):
            sel = html.HtmlSelection()
            self.evtHandler(cell.ConvertToText(sel))
        #super(HtmlView, self).OnCellClicked(cell, x, y, evt)
    def refreshData(self, htmlStr):
        self.SetPage(htmlStr)
        ui_utils.addFullExpandChildComponent(self.Parent, self)
        
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
        ui_utils.addFullExpandChildComponent(self.Parent, self)
        
#========                   
                   
                   
                   
                   
                   
                   
                   
                   
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
    def __init__(self):
        self.pathes = {}#{1:(path1,),}
        
        self.itemColumnStr = None
        self.itemcolumns = []#[[col1,width,align,ro,],]
        self.itemdata = {}#{1:(col1,col2,col3,),}
        #all Items to be saved
        self.displayItemData = {}#displayed in Item List View
        
        self.tagHtmlStr = None
        self.tagHeaderStr = None
        self.tagFooterStr = None
        self.tag2item = {}#{tag1:count,}
        self.tagTemplate = '<tag>[%s]</tag>'
        self.tagSizeTemplate = '<font size=%s>%s</font>'
        self.tagColorTemplate = '<font color=%s>%s</font>'
        self.tagBodyTemplate = '<data>%s</data>'

        self.tagColorDefine = {'sys-%s':'gray', }
        self.tagSizeDefine = {(100,sys.maxint):'+5', (50,99):'+4', (1,10):'-2', (11,49):'+0'}
        
        self.initPath()
        self.initItemsAndColumn()
        self.initTags()
        
        self.refreshObj = {}
        
        #print self.itemcolumns
        #ui_utils.log(str(['%s:%d'%(t,len(i)) for t,i in self.tag2item.items()]))
    
    def syncPath(self):
        pathlist = [p[0] for p in self.pathes.values()]
        for k, i in self.itemdata.items():
            if not SYS_TAG_DEL in i[TAG_COL_IDX].split(';'):
                for p in pathlist:
                    if not p in i[PATH_COL_IDX]:
                        self.dowithTag4Item(k, SYS_TAG_DEL, True)
                        break
                if not os.path.exists(i[PATH_COL_IDX]):
                    self.dowithTag4Item(k, SYS_TAG_DEL, True)
                    
        for p in pathlist:
            for f in os.listdir(p):
                self.addItem(os.path.join(p, f), f)

        
    def refreshAll(self):
        self.buildTagsHtmlStr()
        self.refreshObj[TAG_CONFIG_F_NAME].refreshData(self.tagHtmlStr)
        self.refreshObj[PATH_CONFIG_F_NAME].refreshData(self.pathes)
        self.refreshObj[ITEM_CONFIG_F_NAME].refreshData(self.displayItemData)
    
    def initTags(self):
        self.tagHtmlStr = '\n'.join(io.load(TAG_CONFIG_F_NAME))
        
        ss = re.split(self.tagBodyTemplate%'(.|\n)+', self.tagHtmlStr, flags=re.IGNORECASE)#ignore \n
        self.tagHeaderStr = ss[0]
        self.tagFooterStr = ss[2]
        
        #content inited by items
        self.buildTagsHtmlStr()
    def buildTagsHtmlStr(self):
        tags = []
        for aTag in self.tag2item.keys():
            tags.append(self.tagTemplate%('%s:%d'%(aTag, self.tag2item[aTag])))
        tagStr = '\n'.join(tags)
        
        self.tagHtmlStr = '%s%s%s' % (self.tagHeaderStr, self.tagBodyTemplate%tagStr, self.tagFooterStr)
    def addTag4Item(self, rowKey, newTag):
        self.dowithTag4Item(rowKey, newTag, True)
    def rmvTag4Item(self, rowKey, newTag):
        self.dowithTag4Item(rowKey, newTag, False)
    def dowithTag4Item(self, rowKey, newTag, isAdd):
        itemInAll = self.itemdata[rowKey]
        #itemInDisplay = self.displayItemData[rowKey]
        itemTagStr = itemInAll[TAG_COL_IDX]
        itemTags = itemTagStr.split(';')
        if newTag in itemTags:
            if isAdd:
                ui_utils.warn('add tag fail, %s already set for %d'%(newTag, rowKey))
            else:
                itemTags.remove(newTag)
                if len(itemTags) > 0:
                    itemInAll[TAG_COL_IDX] = ';'.join(itemTags)
                else:
                    itemInAll[TAG_COL_IDX] = ''
                #itemInDisplay[TAG_COL_IDX] = itemInAll[TAG_COL_IDX]
                if not newTag in self.tag2item.keys():
                    ui_utils.warn('tag %s not exists'%newTag)
                elif 1 == self.tag2item[newTag]:
                    self.tag2item.pop(newTag)
                else:
                    self.tag2item[newTag] -= 1
        else:
            if isAdd:
                if len(itemInAll[TAG_COL_IDX]) > 0:
                    itemInAll[TAG_COL_IDX] = '%s;%s' % (itemInAll[TAG_COL_IDX], newTag)
                else:
                    itemInAll[TAG_COL_IDX] = newTag
                #itemInDisplay[TAG_COL_IDX] = itemInAll[TAG_COL_IDX]
                if newTag in self.tag2item.keys():
                    self.tag2item[newTag] += 1
                else:
                    self.tag2item[newTag] = 1
            else:
                ui_utils.warn('rmv tag fail, %s not set for %d'%(newTag, rowKey))
    def filterItemByTag(self, tag):
        if ALL_TAG == tag:
            self.displayItemData = self.itemdata
        else:
            self.displayItemData = {}
            for key, item in self.itemdata.items():
                itemTags = item[TAG_COL_IDX].split(';')
                if tag in itemTags:
                    self.displayItemData[key] = item
    def initItemsAndColumn(self):
        lines = io.load(ITEM_CONFIG_F_NAME)
        
        self.itemColumnStr = lines[0]
        self.itemcolumns = self.initColumns(lines[0])
        
        idx = 0
        for line in lines[1:]:
            linestr = line.split(',')
            self.itemdata[idx] = linestr
            
            tagstr = linestr[-2]
            if len(tagstr) > 0:
                for aTag in tagstr.split(';'):
                    if aTag in self.tag2item.keys():
                        self.tag2item[aTag] += 1
                    else:
                        self.tag2item[aTag] = 1
            
            idx += 1
            
        self.displayItemData = self.itemdata
    def initColumns(self, colStr):
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
    def tostrsItem(self):
        ret = [self.itemColumnStr]
        for i in self.itemdata.values():
            ret.append(','.join(i))
        return ret
    def saveItem(self):
        io.save(self.tostrsItem(), ITEM_CONFIG_F_NAME)
            
    def initPath(self):
        idx = 0
        for line in io.load(PATH_CONFIG_F_NAME):
            self.pathes[idx] = (line.strip(), )
            idx += 1
    def tostrsPath(self):
        return [p[0] for p in self.pathes.values()]
    def savePath(self):
        io.save(self.tostrsPath())
    #def getPathes(self):
    #    return self.pathes
    def _getIdByPath(self, aPath):
        for id in self.pathes.keys():
            if aPath == self.pathes[id][0]:
                return id
        return -1
    def addPath(self, newpath):
        id = self._getIdByPath(newpath)
        if not -1 == id:
            ui_utils.warn('%s already exists'%newpath)
            return False
        else:
            if {} == self.pathes:
                newid = 1
            else:
                newid = max(self.pathes.keys()) + 1
            self.pathes[newid] = (newpath, )
            ui_utils.log('model add %s, pathes count is %d'%(newpath,len(self.pathes.keys())))
            return True
    def rmvPath(self, oldpath):
        id = self._getIdByPath(oldpath)
        if not -1 == id:
            self.pathes.pop(id)
            ui_utils.log('model rmv %s, pathes count is %d'%(oldpath,len(self.pathes.keys())))
            return True
        else:
            ui_utils.warn('%s not exists'%oldpath)
            return False
            
    def _findItem(self, file):
        for f in self.itemdata.values():
            if file == f[1]:
                return True
        return False
    def addItem(self, file, fn):
        found = self._findItem(file)
        if found:
            ui_utils.warn('Item %s already exists'%file)
        else:
            if {} == self.itemdata:
                newid = 1
            else:
                newid = max(self.itemdata.keys()) + 1
                
            if os.path.isfile(file):
                fn = os.path.splitext(fn)[0]#only file name, without ext
            self.itemdata[newid] = [fn,file,'',SYS_TAG_NEW,'']
            self.displayItemData[newid] = self.itemdata[newid]
            
            if SYS_TAG_NEW in self.tag2item.keys():
                self.tag2item[SYS_TAG_NEW] += 1
            else:
                self.tag2item[SYS_TAG_NEW] = 1
            ui_utils.log('Item %s added'%file)
    def rmvItem(self, listKey):
        itemTags = self.itemdata[listKey][TAG_COL_IDX].split(';')
        for itemTag in itemTags:
            if not 0 == len(itemTag):
                self.tag2item[itemTag] -= 1
            if 0 == self.tag2item[itemTag]:
                self.tag2item.pop(itemTag)
        self.itemdata.pop(listKey)
        #self.displayItemData.pop(listKey)
        
#--------BEGIN Controllor
class EventHandler(object):
    def __init__(self, sender, model, mainView, modelKeyColIdx=0):
        self.sender = sender
        self.model = model
        self.mainView = mainView
        self.modelKeyColIdx = modelKeyColIdx
    def listBeginEdit(self, event):#disable edit: path, tags
        '''
        ^ edit grid cell, some column READONLY by 'ro'
        ^ --------
        '''
        if READONLY == self.sender.columns[event.Column][3]:
            event.Veto()#Readonly
        else:
            self.oldval = event.Text
            ui_utils.log('evt edit from %s' % event.Text)
    def listEndEdit(self, event):#edit
        if not self.oldval == event.Text:
            ui_utils.log('evt edit to %s' % event.Text)
            #event.Allow()
            self.model.itemdata[self.sender.GetItemData(self.sender.GetFirstSelected())][event.Column] = event.Text
            self.model.saveItem()
            self.mainView.log('edit cell done')
            del self.oldval
        
    def pathDel(self, event):
        '''
        ^ remove path by click DEL key, multi select is supported
        ^ --------
        '''
        list = self.sender
        selectedRow = list.GetFirstSelected()
        while not -1 == selectedRow:
            selKey = list.GetItem(selectedRow, self.modelKeyColIdx).GetText()
            self.model.rmvPath(selKey)
            ui_utils.log('evt rmv %s'%selKey)
            selectedRow = list.GetNextSelected(selectedRow)
        self.model.refreshAll()
        
        self.model.savePath()
    def itemDel(self, event):
        '''
        ^ remove item by click DEL key, multi select is supported
        ^ --------
        '''
        list = self.sender
        selectedRow = list.GetFirstSelected()
        while not -1 == selectedRow:
            selKey = list.GetItemData(selectedRow)
            self.model.rmvItem(selKey)
            ui_utils.log('evt rmv %d'%selKey)
            selectedRow = list.GetNextSelected(selectedRow)
        self.model.refreshAll()
        
        self.model.saveItem()
    def listRefresh(self, event):
        '''
        ^ refresh item for all pathes by click F5 key
        ^ if +folder-item: add to item
        ^ if -folder+item: tag item with sys-del
        ^ pathes list must be focused
        ^ --------
        '''
        self.model.syncPath()
        self.model.refreshAll()
        self.model.saveItem()
        ui_utils.log('refresh pathes')
    def listSetTag(self, event):
        '''
        ^ set tags of ITEM by click F2 key, multi select is supported
        ^ '+' means add, '-' means del, split tags by ';'
        ^ --------
        '''
        ui_utils.log('set tag')
        dlg = wx.TextEntryDialog(None, "'+' means add, '-' means del, split tags by ';'", 'Set Tag(s)', '')
        if dlg.ShowModal() == wx.ID_OK:
            ui_utils.log(dlg.GetValue())
            
            for newTag in dlg.GetValue().split(';'):
                newTag = newTag.strip()
                self.listSetATag(newTag)
                
            self.model.refreshAll()
            self.model.saveItem()
        dlg.Destroy()

        
    def listSetATag(self, newTag):
        list = self.sender
        selectedRow = list.GetFirstSelected()
        while not -1 == selectedRow:
            rowKey = list.GetItemData(selectedRow)
            if '+' == newTag[:1]:
                self.model.addTag4Item(rowKey, newTag[1:])
            elif '-' == newTag[:1]:
                self.model.rmvTag4Item(rowKey, newTag[1:])
                
            selectedRow = list.GetNextSelected(selectedRow)
        #self.model.buildTagsHtmlStr()
        
    def pathListKeyDown(self, event):
        if wx.WXK_DELETE == event.GetKeyCode():
            self.pathDel(event)
            self.mainView.log('del path done')
        elif wx.WXK_F5 == event.GetKeyCode():
            self.listRefresh(event)
            self.mainView.log('refresh path done')
    def itemListKeyDown(self, event):
        if wx.WXK_DELETE == event.GetKeyCode():
            self.itemDel(event)
            self.mainView.log('del item done')
        elif wx.WXK_F2 == event.GetKeyCode():
            self.listSetTag(event)
            self.mainView.log('set tag for item done')
    
        
    def htmlTagClick(self, tagStr):#select tag
        '''
        ^ filter by click tag
        ^ --------
        '''
        tag = tagStr[1:-1]
        ui_utils.log(tag)#trim []
        self.model.filterItemByTag(tag.split(':')[0])
        self.mainView.log('click tag %s done'%tag)
        
        self.model.refreshAll()
        
    def onDropFile(self, x, y, filenames):#add path
        '''
        ^ drag&drop path to path list
        ^ insert path(es) to tag their sub dirs or files
        ^ --------
        '''
        added = False
        for file in filenames:
            if os.path.isdir(file):
                added = self.model.addPath(file)
                if added:
                    for f in os.listdir(file):
                        self.model.addItem(os.path.join(file, f), f)
            else:
                ui_utils.warn('add path [%s] failed'%file)
            
        if added:
            self.model.refreshAll()
            self.model.saveItem()
            self.model.savePath()
            
            self.mainView.log('add path done')
            
class FileDropTarget(wx.FileDropTarget):
    def __init__(self, window, model, mainView):
        wx.FileDropTarget.__init__(self)  
        self.window = window
        window.SetDropTarget(self)
        self.dropFile = EventHandler(self.window, model, mainView).onDropFile
    def OnDropFiles(self, x, y, filenames):
        self.dropFile(x, y, filenames)            
#--------BEGIN UI
def makeMainWin():
    mainWin = MainWin()
    model = Model()
    
    view1 = SplitView(mainWin.getViewPort())
    
    view2 = HtmlView(view1.p1, EventHandler(None, model, mainWin).htmlTagClick)
    model.refreshObj[TAG_CONFIG_F_NAME] = view2#view2.refreshData(model.tagHtmlStr)
    
    view3 = ListView(view1.p2, (('Pathes', 200, wx.LIST_FORMAT_LEFT, 'ro'), ))
    evtHandler = EventHandler(view3, model, mainWin)
    view3.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler.listBeginEdit)
    view3.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.listEndEdit)
    view3.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.pathListKeyDown)
    FileDropTarget(view3, model, mainWin)
    model.refreshObj[PATH_CONFIG_F_NAME] = view3#view3.refreshData(model.getPathes())
    
    view4 = ListView(view1.p3, model.itemcolumns)
    evtHandler = EventHandler(view4, model, mainWin)
    view4.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler.listBeginEdit)
    view4.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.listEndEdit)
    view4.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.itemListKeyDown)
    model.refreshObj[ITEM_CONFIG_F_NAME] = view4#view4.refreshData(model.displayItemData)
            
    model.refreshAll()
    mainWin.log('show me done')

    mainWin.show()
    












          
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

if "__main__" == __name__:
    makeMainWin()

'''
^ name: tag tool
^ author: tillfall(tillfall@126.com)
^ version: 3.1
^ create: 2016-02-21
^ release: 2016-02-28
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
import datetime
import unittest
import locale
import shutil

#USER DEFINE
ADD_ITEM_RECURSION = False
SYS_TAG_NEW = '[NEW]'
SYS_TAG_DEL = '[DEL]'
SYS_TAG_RMV = '[RMV]'
TAG_COLOR_AND_SIZE = {SYS_TAG_NEW:('blue', '+5', 'I'), SYS_TAG_RMV:('green', '+5', 'I'),}

#SYSTEM DEFINE
PATH_CONFIG_F_NAME = '__pathes.txt'
ITEM_CONFIG_LINK = '__items_link.txt'#use remote file to save item data
ITEM_CONFIG_F_NAME = '__items.txt'
EXT_CONFIG_F_NAME = '__ext.txt'
BLACK_LIST_F_NAME = '__blacklist.txt'
FILTER_CONFIG_F_NAME = '__filters.txt'
TAG_CONFIG_F_NAME = '___tag.txt'

READONLY = 'ro'
ALL_TAG ='ALL'

TAG_COL_IDX = 3
PATH_COL_IDX = 1

ENCODING = 'gbk'

HELP = 'F2:SyncPath, F3:Clear, F4:SetColumn; F5:SelectAll, F6:SortPathRev, F7:OpenUpperDir, F8:Open; F9:SetTag, F10:AutoTag, F11:NEW, F12:DEL'

class ui_utils(object):
    _log_inited = False
    @staticmethod
    def today():
        return datetime.datetime.now().strftime('%Y-%m-%d')
    @staticmethod
    def bckfile(filename):
        itemfileinfo = os.path.splitext(filename)
        bckfile = '%s_%s%s'%(itemfileinfo[0], datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), itemfileinfo[1])
        shutil.copy(filename, bckfile)
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
    def addFullExpandChildComponent(child):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(child, 1, wx.EXPAND)
        child.Parent.SetSizer(sizer)
        child.Parent.SetAutoLayout(True)
        
        child.SetSize(child.Parent.GetSize())
        child.SetBackgroundColour(child.Parent.GetBackgroundColour())
        
    @staticmethod
    def getSubFiles(rootpath):
        ret = []
        if ADD_ITEM_RECURSION:
            for root, dirs, files in os.walk(rootpath):
                for file in files:#do not include folder
                    ret.append((os.path.join(root, file), file))
        else:
            for file in os.listdir(rootpath):
                ret.append((os.path.join(rootpath, file), file))
        return ret
        
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
        
class HtmlView(html.HtmlWindow):
    def __init__(self, parent):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
    def registerTagClick(self, evtHandler):
        self.evtHandler = evtHandler
    def OnCellClicked(self, cell, x, y, evt):
        if isinstance(cell, html.HtmlWordCell):
            sel = html.HtmlSelection()
            self.evtHandler(cell.ConvertToText(sel))
        #super(HtmlView, self).OnCellClicked(cell, x, y, evt)
    def refreshData(self, htmlStr):
        self.SetPage(htmlStr)
        #ui_utils.addFullExpandChildComponent(self)
        
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
        self._initColumns()
        
        self.allItemDataMap = {}
        self.itemDataMap = {}
        
    def _initColumns(self):
        i = 0
        for col in self.columns:
            self.InsertColumn(i, col[0], col[2])#name, align
            self.SetColumnWidth(i, col[1])#width
            i += 1
        
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self
    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)
        
    def onRevSort(self, colIdx):
        _defaultSorter = self.GetColumnSorter
        self.GetColumnSorter = self.GetColumnSorterRev
        self.SortListItems(colIdx, int(not self._colSortFlag[colIdx]))
        self.GetColumnSorter = _defaultSorter
    def __revpath(self, p):
        fs = p.split(os.path.sep)
        fs.reverse()
        return os.path.sep.join(fs)
    def GetColumnSorterRev(self):
        return self.__ColumnSorterRev
    def __ColumnSorterRev(self, key1, key2):#copy from ColumnSorterMixin.__ColumnSorter
        col = self._col
        ascending = self._colSortFlag[col]
        item1 = self.itemDataMap[key1][col]
        item2 = self.itemDataMap[key2][col]
        #rev begin
        item1 = self.__revpath(item1)
        item2 = self.__revpath(item2)
        #rev end

        #--- Internationalization of string sorting with locale module
        if type(item1) == unicode and type(item2) == unicode:
            cmpVal = locale.strcoll(item1, item2)
        elif type(item1) == str or type(item2) == str:
            cmpVal = locale.strcoll(str(item1), str(item2))
        else:
            cmpVal = cmp(item1, item2)
        #---

        # If the items are equal then pick something else to make the sort value unique
        if cmpVal == 0:
            cmpVal = apply(cmp, self.GetSecondarySortValues(col, key1, key2))

        if ascending:
            return cmpVal
        else:
            return -cmpVal
    
    def readonlyCell(self, event):#disable edit: path, tags
        event.Veto()#Readonly
        
    def addRow(self, rowInfo):
        id = max(self.allItemDataMap.keys()) + 1
        self.allItemDataMap[id] = rowInfo
        self.itemDataMap[id] = rowInfo
        index = self.InsertStringItem(sys.maxint, rowInfo[0])
        for i in range(1, len(rowInfo)):
            self.SetStringItem(index, i, rowInfo[i])
        self.SetItemData(index, id)
    def showRow(self, dataId):
        rowInfo = self.allItemDataMap[dataId]
        self.itemDataMap[dataId] = rowInfo
        index = self.InsertStringItem(sys.maxint, rowInfo[0])
        for i in range(1, len(rowInfo)):
            self.SetStringItem(index, i, rowInfo[i])
        self.SetItemData(index, dataId)
    def delRow(self, rowId):
        dataId = self.GetItemData(rowId)
        self.allItemDataMap.pop(dataId)
        self.itemDataMap.pop(dataId)
        self.DeleteItem(rowId)
    def hideRow(self, rowId):
        dataId = self.GetItemData(rowId)
        self.itemDataMap.pop(dataId)
        self.DeleteItem(rowId)
        return dataId
    def clear(self):
        self.itemDataMap = {}
        self.allItemDataMap = {}
        self.ClearAll()
        
    def modRow(self, rowId, colId, newVal, setView=False):
        dataId = self.GetItemData(rowId)
        self.allItemDataMap[dataId][colId] = newVal
        
        #self.itemDataMap[dataId][colId] = newVal
        if setView:
            self.SetStringItem(rowId, colId, newVal)
        
class MainWin(wx.App):
    def __init__(self):
        wx.App.__init__(self, redirect=False)
        self.evtHandler = {}
        
    def BindToolbarEvent(self, evtId, evtHandler):
        self.evtHandler[evtId] = evtHandler
    def _OnToolClick(self, event):
        self.evtHandler[event.GetId()]()
    def _initToolbarOneBtn(self, _id, bmp):
        self.tb.AddLabelTool(_id, bmp[1], bmp[0], shortHelp=bmp[1], longHelp=bmp[1])
        self.Bind(wx.EVT_TOOL, self._OnToolClick, id=_id)
    def _initToolBarBtn(self):
        tsize = (24,24)
        sync_bmp =  (wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, tsize), 'sync')
        clr_bmp =  (wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_TOOLBAR, tsize), 'clear')
        all_bmp = (wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_TOOLBAR, tsize), 'select all')
        sortRvt_bmp = (wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, tsize), 'sort reverse')
        openDir_bmp = (wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize), 'open dir')
        open_bmp = (wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, tsize), 'open')
        setTag_bmp = (wx.ArtProvider.GetBitmap(wx.ART_NEW_DIR, wx.ART_TOOLBAR, tsize), 'set tag')
        autoTag_bmp = (wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize), 'auto tag')
        newTag_bmp = (wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, tsize), 'tag NEW')
        delTag_bmp = (wx.ArtProvider.GetBitmap(wx.ART_DEL_BOOKMARK, wx.ART_TOOLBAR, tsize), 'tag DEL')
        batSet_bmp = (wx.ArtProvider.GetBitmap(wx.ART_HELP_SETTINGS, wx.ART_TOOLBAR, tsize), 'multi set')
        #see ico from http://blog.csdn.net/rehung/article/details/1859030
        #id same with Fx key
        self._initToolbarOneBtn(20, sync_bmp)
        self._initToolbarOneBtn(30, clr_bmp)
        self._initToolbarOneBtn(40, batSet_bmp)
        self.tb.AddSeparator()
        self._initToolbarOneBtn(50, all_bmp)
        self._initToolbarOneBtn(60, sortRvt_bmp)
        self._initToolbarOneBtn(70, openDir_bmp)
        self._initToolbarOneBtn(80, open_bmp)
        self.tb.AddSeparator()
        self._initToolbarOneBtn(90, setTag_bmp)
        self._initToolbarOneBtn(100, autoTag_bmp)
        self._initToolbarOneBtn(110, newTag_bmp)
        self._initToolbarOneBtn(120, delTag_bmp)
        self.tb.AddSeparator()
        self.tb.AddSeparator()
        
    def OnInit(self):
        frame = wx.Frame(None, -1, "tagger  --  [%s]"%HELP, pos=(50,50), size=(1280,600),
                        style=wx.DEFAULT_FRAME_STYLE, name="tagger")
        self.sb = frame.CreateStatusBar()
        #self.sb.SetFieldsCount(2)
        
        self.tb = frame.CreateToolBar(( wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT))
        self._initToolBarBtn()
        
        #self.tb.AddStretchableSpace()#right align
        self.search = TestSearchCtrl(self.tb, size=(600, -1), doSearch=self._search)
        self.search.SetDescriptiveText('example: row[?] == u"xxx" or u"xxx" in row[?]. string  must be lead by u, especially for chinese')
        self.tb.AddControl(self.search)
        self.tb.Realize()
        
        frame.Show(True)
        frame.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        self.SetTopWindow(frame)
        self.frame = frame
        
        #self.sb.PushStatusText(HELP, 2)
        return True
        
    def OnExitApp(self, evt):
        self.frame.Close(True)
    def OnCloseFrame(self, evt):
        if hasattr(self, "window") and hasattr(self.window, "ShutdownDemo"):
            self.window.ShutdownDemo()
        evt.Skip()
        
    def setToolbarDefaultFilter(self, filters):
        self.search.setDefaultFilter(filters)
    def registerSearcher(self, searcher):
        self._searchImpl = searcher
    def _search(self, text):
        self._searchImpl(text)
        
    def log(self, text, onErr=False):
        if not onErr:
            self.sb.PushStatusText(text)
        else:
            _dlg = wx.MessageDialog(None, text, 'ERROR', wx.OK | wx.ICON_ERROR)
            _dlg.ShowModal()
            _dlg.Destroy()
        
    def getViewPort(self):
        return self.frame
        
class TestSearchCtrl(wx.SearchCtrl):
    maxSearches = 20
    
    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.doSearch = doSearch
        self.searches = []

    def setDefaultFilter(self, filters):
        self.searches = filters
        self.SetMenu(self.MakeMenu())
        self.SetValue('')
        
    def OnTextEntered(self, evt):
        text = self.GetValue()
        
        self.doSearch(text)
        if not text in self.searches:
            self.searches.insert(0, text)#recent search in the front
        if len(self.searches) > self.maxSearches:
            del self.searches[-1]#fix a bug: delete older filter
        self.SetMenu(self.MakeMenu())
        self.SetValue("")
        
    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        self.doSearch(text)
        
    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            if '' == txt.strip():
                continue
            menu.Append(1+idx, txt)
        return menu        

backuped = False
class io(object):
    @staticmethod
    def load(fname=PATH_CONFIG_F_NAME):
        lines = []
        if os.path.isfile(fname):
            file = codecs.open(fname, 'r', ENCODING)
            lines = [x.strip() for x in file.readlines()]
            file.close()
            ui_utils.log('load %s, %d lines' % (fname, len(lines)))
        return lines
    @staticmethod
    def save(lst, fname, comfirm=False):#not implement now
        if comfirm:
            _dlg = wx.MessageDialog(None, 'Some Important CHANGEs made, SAVE it or not?', '!!!', wx.YES_NO | wx.ICON_EXCLAMATION)
            ret = _dlg.ShowModal()
            _dlg.Destroy()
            if not wx.ID_YES == ret:
                return
        
        global backuped
        if not backuped:
            ui_utils.log('backup items')
            ui_utils.bckfile(ITEM_CONFIG_F_NAME)
            backuped = True
        
        file = codecs.open(fname, 'w', ENCODING)
        for l in lst:
            try:
                file.write('%s\n'%l)
            except Exception,e:
                ui_utils.error(l)
                raise e
        file.close()
        ui_utils.log('save %s, %d lines' % (fname, len(lst)))

class FileDropTarget(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)  
        window.SetDropTarget(self)
    def registerPathAdd(self, evt):
        self.dropFile = evt
    def OnDropFiles(self, x, y, filenames):
        self.dropFile(x, y, filenames)            
        
#BEGIN EVENT STUB
class EvtStub(object):
    def __init__(self, sender):
        self.sender = sender
    def handler(self, *args):
        print '%s:%s' % (self.sender, args) 
#END EVENT STUB

class EventHandler(object):
    def __init__(self, sender):
        self.sender = sender
    def itemEdit(self):
        pass
    def itemBatchEdit_F4(self):
        pass
    def itemSetTag_F9(self):
        pass
    def itemAutoTag_F10(self):
        pass
    def itemNewTag_F11(self):
        pass
    def itemDelTag_F12(self):
        pass
    def itemDel(self):
        pass
    def pathDel(self):
        pass
    def itemSelectAll_F5(self):
        pass
    def itemSortRev_F6(self):
        pass
    def itemOpenDir_F7(self):
        pass
    def itemOpen_F8(self):
        pass
    def pathSync_F2(self):
        pass
    def pathClear_F2(self):
        pass
    def pathAdd_Drop(self):
        pass
    def itemFilterByInput(self):
        pass
    def itemFilterByTag(self):
        pass

def makeMainWin():
    mainWin = MainWin()
    
    #BEGIN EVENT STUB
    view1 = SplitView(mainWin.getViewPort())
    view2 = HtmlView(view1.p1)
    view3 = ListView(view1.p2, (('Pathes', 200, wx.LIST_FORMAT_LEFT, 'ro'), ))    
    
    mainWin.registerSearcher(EvtStub('searcher').handler)
    for evtId in (20,30,40,50,60,70,80,90,100,110,120):
        mainWin.BindToolbarEvent(evtId, EvtStub(str(evtId)).handler)
    view2.registerTagClick(EvtStub('tag filter').handler)
    view2.refreshData('\n'.join(io.load('___tag.txt')))
    FileDropTarget(view2).registerPathAdd(EvtStub('file drop').handler)
    listctrldata = {
        1 : ["Hey!"],
        2 : ["Try changing the contents"],
        3 : ["in"],
        4 : ["See how the length columns"],
        5 : ["You can use"],
        6 : ["and cursor up"],
        }
    for key, val in listctrldata.items():
        view3.itemDataMap[key] = val
        view3.allItemDataMap[key] = val
    for key, data in listctrldata.items():
        index = view3.InsertStringItem(sys.maxint, data[0])
        view3.SetItemData(index, key)
        
    ui_utils.addFullExpandChildComponent(view2)
    ui_utils.addFullExpandChildComponent(view3)

    view3.delRow(2)
    id = view3.hideRow(4)
    view3.showRow(id)
    view3.addRow(['mlkcadf'])
    view3.modRow(4, 0, 'hello world', True)
    #view3.clear()
    

    #END EVENT STUB

    mainWin.log('show me done')
    mainWin.MainLoop()

if "__main__" == __name__:
    if 2 == len(sys.argv):
        #global PATH_CONFIG_F_NAME, ITEM_CONFIG_F_NAME, EXT_CONFIG_F_NAME, BLACK_LIST_F_NAME, FILTER_CONFIG_F_NAME
        PATH_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], PATH_CONFIG_F_NAME[1:])
        ITEM_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], ITEM_CONFIG_F_NAME[1:])
        EXT_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], EXT_CONFIG_F_NAME[1:])
        BLACK_LIST_F_NAME = '_%s%s' % (sys.argv[1], BLACK_LIST_F_NAME[1:])
        FILTER_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], FILTER_CONFIG_F_NAME[1:])
        ITEM_CONFIG_LINK = '_%s%s' % (sys.argv[1], ITEM_CONFIG_LINK[1:])
    makeMainWin()
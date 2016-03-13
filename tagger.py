'''
^ name: tag tool
^ author: tillfall(tillfall@126.com)
^ version: 4.0
^ create: 2016-02-21
^ release: 2016-03-10
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
import copy

#USER DEFINE
SYS_TAG_NEW = '[NEW]'
SYS_TAG_DEL = '[DEL]'
SYS_TAG_RMV = '[RMV]'
TAG_COLOR_AND_SIZE = {SYS_TAG_NEW:('blue', '+5', 'I'), SYS_TAG_RMV:('green', '+5', 'I'),}

#SYSTEM DEFINE
ADD_ITEM_RECURSION = '__RECURSION.txt'
ADD_ALL_RECURSION = '__RECURSION_ALL.txt'
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
COMMENT_COL_IDX = 5

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
        if os.path.isfile(ADD_ALL_RECURSION):
            print 'RECURSION ALL'
            for root, dirs, files in os.walk(rootpath):
                for file in files:#do not include folder
                    ret.append((os.path.join(root, file), file))
                for dir in dirs:
                    ret.append((os.path.join(root, dir), '[%s]'%dir))
        elif os.path.isfile(ADD_ITEM_RECURSION):
            print 'RECURSION'
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
    #def refreshData(self, htmlStr):
    #    self.SetPage(htmlStr)
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
        if len(self.allItemDataMap) == 0:
            id = 1
        else:
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
    def showAll(self):
        for dataId in self.allItemDataMap.keys():
            if not dataId in self.itemDataMap.keys():
                self.showRow(dataId)
        
    def modRow(self, rowId, colId, newVal, setView=False):
        dataId = self.GetItemData(rowId)
        self.allItemDataMap[dataId][colId] = newVal
        
        #self.itemDataMap[dataId][colId] = newVal
        if setView:
            self.SetStringItem(rowId, colId, newVal)
    def modRowByExec(self, rowId, execStr):
        dataId = self.GetItemData(rowId)
        row = self.allItemDataMap[dataId]
        oldRowData = copy.copy(row)
        
        exec(execStr)
        for i in range(len(oldRowData)):
            if not oldRowData[i] == row[i]:
                self.SetStringItem(rowId, i, row[i])
                return
                
    def delRow(self, rowId):#TBD
        dataId = self.GetItemData(rowId)
        self.allItemDataMap.pop(dataId)
        self.itemDataMap.pop(dataId)
        self.DeleteItem(rowId)
    def hideRow(self, rowId):#TBD
        dataId = self.GetItemData(rowId)
        self.itemDataMap.pop(dataId)
        self.DeleteItem(rowId)
        return dataId
    def clear(self):
        self.itemDataMap = {}
        self.allItemDataMap = {}
        #self.ClearAll()
        self.DeleteAllItems()
    def delSelectedRows(self):
        rowId = self.GetFirstSelected()
        while not -1 == rowId:
            self.delRow(rowId)            
            rowId = self.GetFirstSelected()
        
    def getText(self, rowId, colId):
        return self.GetItem(rowId, colId).GetText()
    def getFirstSelectedText(self, colId):
        return self.getText(self.GetFirstSelected(), colId)
    def selectAll(self):
        for i in range(self.GetItemCount()):
            self.Select(i)
    def getSelectedRowId(self):
        ret = []
        rowId = self.GetFirstSelected()
        while not -1 == rowId:
            ret.append(rowId)            
            rowId = self.GetNextSelected(rowId)
            
        return ret
        
        
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
        
        user1_bmp = (wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_TOOLBAR, tsize), 'print tags')
        user2_bmp = (wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_TOOLBAR, tsize), 'get size')
        user3_bmp = (wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_TOOLBAR, tsize), 'print item')
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
        self._initToolbarOneBtn(910, user1_bmp)
        self._initToolbarOneBtn(920, user2_bmp)
        self._initToolbarOneBtn(930, user3_bmp)
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
            self.sb.PushStatusText(str(text))
        else:
            _dlg = wx.MessageDialog(None, str(text), 'ERROR', wx.OK | wx.ICON_ERROR)
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
        
class Model(object):
    def __init__(self):
        #use remote file to save item data
        lines = io.load(ITEM_CONFIG_LINK)
        if 1 <= len(lines):
            global ITEM_CONFIG_F_NAME
            ITEM_CONFIG_F_NAME = lines[0]
            
        self.tagdata = {}#{tag1:count,}
        self.tagHtmlStr = None
        self.tagHeaderStr = None
        self.tagFooterStr = None
        self.tagTemplate = '<tag>[%s]</tag>'
        self.tagBodyTemplate = '<data>%s</data>'
        self.tagFontTemplate = '<font color="%s"><font size="%s"><%s>%s</%s></font></font>'

        self.pathdata = {}#{1:(path1,),}
        
        self.itemdata = {}#{1:(col1,col2,col3,),}
        #all Items to be saved
        self.itemcolumns = []#[[col1,width,align,ro,],]
        self.itemColumnStr = None
        
        self.ext = {}
        
        self.blacklist = []
        
        self.defaultFilters = []
        
        self.filterTag = ALL_TAG
        self.filterStrs = []
        self.filterLogTemplate = 'count: {%d}, tag: {%s}, formular: {%s}'
        
        #self.tagSizeTemplate = '<font size=%s>%s</font>'
        #self.tagColorTemplate = '<font color=%s>%s</font>'
        #self.tagColorDefine = {'sys-%s':'gray', }
        #self.tagSizeDefine = {(100,sys.maxint):'+5', (50,99):'+4', (1,10):'-2', (11,49):'+0'}
        
        self._initPath()
        self._initItemsAndColumn()
        self._initTagHtml()
        self._initExt()
        self._initBlacklist()
        self._initFilters()
        
        #self._buildTagsHtmlStr()
    def _initPath(self):
        idx = 0
        for line in io.load(PATH_CONFIG_F_NAME):
            self.pathdata[idx] = (line.strip(), )
            idx += 1
    def _initBlacklist(self):
        self.blacklist = io.load(BLACK_LIST_F_NAME)
    def _initExt(self):
        for line in io.load(EXT_CONFIG_F_NAME):
            line = line.strip()
            _ss = line.split(':')
            _exts = _ss[1].split(';')
            for _ext in _exts:
                self.ext[_ext] = _ss[0]
    def _initFilters(self):
        self.defaultFilters = io.load(FILTER_CONFIG_F_NAME)
    def _initTagHtml(self):
        self.tagHtmlStr = '\n'.join(io.load(TAG_CONFIG_F_NAME))
        
        ss = re.split(self.tagBodyTemplate%'(.|\n)+', self.tagHtmlStr, flags=re.IGNORECASE)#ignore \n
        self.tagHeaderStr = ss[0]
        self.tagFooterStr = ss[2]
        
        #content inited by items
        #self._buildTagsHtmlStr()
    def buildTagsHtmlStr(self):
        _tags = []
        for aTag, aCount in sorted(self.tagdata.items()):#tag sort
            _tagHtmlStr = self.tagTemplate%('%s:%d'%(aTag, aCount))
            if aTag in TAG_COLOR_AND_SIZE.keys():
                _tagHtmlStr = self.tagFontTemplate%(TAG_COLOR_AND_SIZE[aTag][0], TAG_COLOR_AND_SIZE[aTag][1], TAG_COLOR_AND_SIZE[aTag][2], \
                    _tagHtmlStr, TAG_COLOR_AND_SIZE[aTag][2])
            _tags.append(_tagHtmlStr)
        tagStr = '\n'.join(_tags)
        
        self.tagHtmlStr = '%s%s%s' % (self.tagHeaderStr, self.tagBodyTemplate%tagStr, self.tagFooterStr % len(self.itemdata))
    def _initItemsAndColumn(self):
        lines = io.load(ITEM_CONFIG_F_NAME)
        
        self.itemColumnStr = lines[0]
        self._initColumns(lines[0])
        
        idx = 0
        for line in lines[1:]:
            #empty line
            if len(line.strip()) < 2:
                continue
            linestr = line.split(',')
            
            self._initOneItemRow(idx, linestr)#fix bug when data field count less than column count
            
            tagstr = linestr[TAG_COL_IDX]#tag
            if len(tagstr) > 0:
                for aTag in tagstr.split(';'):
                    self._incTag(aTag)
            idx += 1
            
    def _initOneItemRow(self, idx, values):
        self.itemdata[idx] = values
        for i in range(len(values), len(self.itemcolumns)):
            self.itemdata[idx].append('')
        
    def _initColumns(self, colStr):
        columns = []
        for col in colStr.split(','):
            attrs = col.split(';')
            column = []
            column.append(attrs[0])#name
            column.append(int(attrs[1]))#width
            if 'left' in attrs[2].lower():
                column.append(wx.LIST_FORMAT_LEFT)
            else:
                column.append(wx.LIST_FORMAT_RIGHT)#align
            column.append(attrs[3])#ro
            columns.append(column)
        self.itemcolumns = columns
        
        
    def _incTag(self, aTag):
        if '' == aTag:
            #ui_utils.warn('empty tag inc')
            return
        if aTag in self.tagdata.keys():
            self.tagdata[aTag] += 1
        else:
            self.tagdata[aTag] = 1
    def _decTag(self, aTag):
        if '' == aTag:
            #ui_utils.warn('empty tag dec')
            return
        if aTag in self.tagdata.keys():
            self.tagdata[aTag] -= 1
            if 0 == self.tagdata[aTag]:
                self.tagdata.pop(aTag)
        else:
            #ui_utils.warn('dec tag when not exists')
            pass
    def _newid(self, dict):
        if {} == dict:
            return 1
        else:
            return max(dict.keys()) + 1
        
    def saveItem(self, comfirm=False):
        _tostrsItem = [self.itemColumnStr]
        for i in self.itemdata.values():
            _tostrsItem.append(','.join(i))
        io.save(_tostrsItem, ITEM_CONFIG_F_NAME, comfirm)
        
    def savePath(self, comfirm=False):
        io.save([p[0] for p in self.pathdata.values()], PATH_CONFIG_F_NAME, comfirm)

def errmsg(func):
    def _errmsg(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            _dlg = wx.MessageDialog(None, str(e), 'ERROR', wx.OK | wx.ICON_ERROR)
            _dlg.ShowModal()
            _dlg.Destroy()
            raise e
        return ret
    return _errmsg

class EventHandler(object):
    def __init__(self, tagView, pathView, itemView, model, winlog):
        self.tagView = tagView
        self.pathView = pathView
        self.itemView = itemView
        self.model = model
        self.winlog = winlog
        
    def _setTags(self, rowId, newtags, setView=True):
        tagstr = self.itemView.getText(rowId, TAG_COL_IDX)
        tags = [x.strip() for x in tagstr.split(';')]
        if [''] == tags:
            tags = []
        
        if '-' == newtags:
            for aTag in tags:
                self._setTag(tags, aTag, '-')
            newtaglist = []
        elif '%s%s'%('$',SYS_TAG_DEL) == newtags:
            if SYS_TAG_DEL in tags:
                newtaglist = copy.copy(tags)
                self._setTag(tags, SYS_TAG_DEL, '-')
                newtaglist.remove(SYS_TAG_DEL)
            else:
                for aTag in tags:
                    self._setTag(tags, aTag, '-')
                self._setTag(tags, SYS_TAG_DEL, '+')
                newtaglist = [SYS_TAG_DEL]
        else:
            newtags = newtags.split(';')
            newtaglist = copy.copy(tags)
            for aTag in newtags:
                ret = self._setTag(tags, aTag[1:], aTag[0])
                if '+' == ret:
                    newtaglist.append(aTag[1:])
                elif '-' == ret:
                    newtaglist.remove(aTag[1:])
        
        if setView:
            if 0 == len(newtaglist):
                newtagstr = ''
            elif 1 == len(newtaglist):
                newtagstr = newtaglist[0]
            else:
                newtagstr = ';'.join(sorted(newtaglist))
            
            self.itemView.modRow(rowId, TAG_COL_IDX, newtagstr, True)                
    def _setTag(self, tags, aTag, action):#return + when add, - when del, '' when do nothing
        if '+' == action:
            if not aTag in tags:
                self.model._incTag(aTag)
                return '+'
        elif '-' == action:
            if aTag in tags:
                self.model._decTag(aTag)
                return '-'
        elif '$' == action:
            if aTag in tags:
                return self._setTag(tags, aTag, '-')
            else:
                return self._setTag(tags, aTag, '+')
                
        return ''
        
    @errmsg
    def itemEdit(self, event):
        if not self.oldval == event.Text:
            self.itemView.modRow(event.GetIndex(), event.GetColumn(), event.Text)
            self.model.saveItem()
        del self.oldval
    @errmsg
    def itemBatchEdit_F4(self):
        _dlg = wx.TextEntryDialog(None, "row[?] = u'xxx'", 'Set Cells for Multi Rows')
        if _dlg.ShowModal() == wx.ID_OK:
            setNewValue = _dlg.GetValue()
            
            for i in self.itemView.getSelectedRowId():
                self.itemView.modRowByExec(i, setNewValue)
            self.model.saveItem()
        _dlg.Destroy()
    @errmsg
    def itemSetTag_F9(self):
        _dlg = wx.TextEntryDialog(None, "'+' means add, '-' means del, split tags by ';'", 'Set Tag(s)')
        if _dlg.ShowModal() == wx.ID_OK:
            for rowId in self.itemView.getSelectedRowId():
                self._setTags(rowId, _dlg.GetValue())
        _dlg.Destroy()
        self.model.saveItem()
        self.repaintTagView()
    @errmsg
    def itemAutoTag_F10(self):
        for rowId in self.itemView.getSelectedRowId():
            filepath = self.itemView.getText(rowId, PATH_COL_IDX)
            if os.path.isfile(filepath):
                _ext = os.path.splitext(filepath)[1].lower()
                if not '' == _ext:
                    if _ext in self.model.ext.keys():
                        self._setTags(rowId, '+%s;-%s'%(self.model.ext[_ext], _ext))
                    else:
                        self._setTags(rowId, '+%s'%_ext)
        self.model.saveItem()
        self.repaintTagView()
    @errmsg
    def itemNewTag_F11(self):
        for rowId in self.itemView.getSelectedRowId():
            self._setTags(rowId, '%s%s'%('$', SYS_TAG_NEW))
        self.model.saveItem()
        self.repaintTagView()
    @errmsg
    def itemDelTag_F12(self):
        for rowId in self.itemView.getSelectedRowId():
            self._setTags(rowId, '%s%s'%('$', SYS_TAG_DEL))
        self.model.saveItem()
        self.repaintTagView()
    @errmsg
    def itemDel(self):
        _dlg = wx.MessageDialog(None, 'DELETE', '!!!', wx.YES_NO | wx.ICON_EXCLAMATION)
        if wx.ID_YES == _dlg.ShowModal():
            for rowId in self.itemView.getSelectedRowId():
                self._setTags(rowId, '-', False)
            self.itemView.delSelectedRows()
            
            self.model.itemdata = self.itemView.allItemDataMap
            self.model.saveItem()
            
            self.repaintTagView()
            
            self.winlog(len(self.itemView.itemDataMap))
        _dlg.Destroy()
    @errmsg
    def pathDel(self):
        _dlg = wx.MessageDialog(None, 'DELETE', '!!!', wx.YES_NO | wx.ICON_EXCLAMATION)
        if wx.ID_YES == _dlg.ShowModal():
            self.pathView.delSelectedRows()
            
            self.model.pathdata = self.pathView.allItemDataMap
            self.model.savePath()
            
            #self.repaintTagView()
        _dlg.Destroy()
    @errmsg
    def itemSelectAll_F5(self):#stop here
        self.itemView.selectAll()
    @errmsg
    def itemSortRev_F6(self):#stop here
        self.itemView.onRevSort(PATH_COL_IDX)
    @errmsg
    def itemOpenDir_F7(self):#stop here
        os.startfile(os.path.dirname(self.itemView.getText(self.itemView.GetFirstSelected(), PATH_COL_IDX)))
    @errmsg
    def itemOpen_F8(self):#stop here
        os.startfile(self.itemView.getText(self.itemView.GetFirstSelected(), PATH_COL_IDX))
    @errmsg
    def pathSync_F2(self):
        pathlist = [p[0] for p in self.model.pathdata.values()]#all pathes
        self.itemView.showAll()
        rowId = 0
        while rowId < self.itemView.GetItemCount():
            if not SYS_TAG_RMV in self.itemView.getText(rowId, TAG_COL_IDX).split(';'):
                _inPath = False
                for p in pathlist:#do with items not under path
                    if p in self.itemView.getText(rowId, PATH_COL_IDX):
                        _inPath = True
                        break
                        
                if not _inPath or not os.path.exists(self.itemView.getText(rowId, PATH_COL_IDX)):
                    self._setTags(rowId, '+%s'%SYS_TAG_RMV)#soft delete item
            rowId += 1
                    
        for p in pathlist:
            for f in ui_utils.getSubFiles(p):
                self._addItem(f[0], f[1])
                
        self.model.itemdata = self.itemView.allItemDataMap
        self.model.saveItem()
        self.repaintTagView()
        
        self.winlog(len(self.itemView.itemDataMap))
    @errmsg
    def pathClear_F3(self):
        _dlg = wx.MessageDialog(None, 'ALL DATA WILL BE CLEARED. but no data saved until new data added', '!!!', wx.YES_NO | wx.ICON_EXCLAMATION)
        if wx.ID_YES == _dlg.ShowModal():
            self.itemView.clear()
            self.pathView.clear()
            self.model.tagdata = {}
            self.model.itemdata = {}
            self.model.pathdata = {}
            #self.tagView.SetPage('')
            self.repaintTagView()
        _dlg.Destroy()
        
    def _addPathOnly(self, newpath):#called by addPath. not care items
        if not os.path.sep == newpath[-1]:
            newpath = '%s%s'%(newpath, os.path.sep)#fix bug when a path aaa and another path aaa-bbb, rmv aaa-bbb, it's children will not be rmv
            
        for p in self.model.pathdata.values():
            #if newpath.startswith(p[0]):#fix bug: if upper path added, child path can't be added anymore
            if newpath == p[0]:#do not change. because there is difference under NO recursion mode
                return False
                
        self.pathView.addRow([newpath])
        #ui_utils.log('model add %s, pathdata count is %d'%(newpath,len(self.pathdata.keys())))
        return True
    def _addItem(self, filepath, filename):#called by addPath or syncPath, NO LOG when already exists
        for i_blackrule in self.model.blacklist:
            if eval(i_blackrule):
                ui_utils.warn('%s matches %s'%(filepath, i_blackrule))
                return False
                
        for f in self.model.itemdata.values():
            if filepath == f[1]:
                return False
                
        if os.path.isfile(filepath):
            filename = os.path.splitext(filename)[0]#only file name, without ext
        #self.itemdata[newid] = [filename,filepath,ui_utils.today(),SYS_TAG_NEW,'']
        self.itemView.addRow([filename,filepath,ui_utils.today(),SYS_TAG_NEW])#fix bug: add item with less field
        
        self.model._incTag(SYS_TAG_NEW)
        return True
        #ui_utils.log('Item %s added'%filepath)
        
    @errmsg
    def pathAdd_Drop(self, x, y, filenames):
        for file in filenames:
            if os.path.isdir(file):
                thispathadded = self._addPathOnly(file)#path added
                if thispathadded:
                    for f in ui_utils.getSubFiles(file):
                        self._addItem(f[0], f[1])#path, filename #UnicodeDecodeError
        
        self.model.pathdata = self.pathView.allItemDataMap
        self.model.itemdata = self.itemView.allItemDataMap
        self.model.savePath()
        self.model.saveItem()
        self.repaintTagView()
        
        self.winlog(len(self.itemView.itemDataMap))
                
    @errmsg
    def itemFilterByInput(self, text):
        if '' == text.strip():
            self.itemView.showAll()
        else:
            rowId = 0
            while rowId < self.itemView.GetItemCount():
                row = self.itemView.itemDataMap[self.itemView.GetItemData(rowId)]
                if not eval(text):
                    self.itemView.hideRow(rowId)
                else:
                    rowId += 1
                    
        self.winlog(len(self.itemView.itemDataMap))
    @errmsg
    def itemFilterByTag(self, tagStr):#too slow
        tag = tagStr[1:-1]
        tag = tag.split(':')[0]
        if ALL_TAG == tag:
            self.itemView.showAll()
        else:
            '''
            rowId = 0
            while rowId < self.itemView.GetItemCount():
                tags = self.itemView.getText(rowId, TAG_COL_IDX)
                if tag in tags:
                    rowId += 1
                else:
                    self.itemView.hideRow(rowId)
            '''
            self.itemView.itemDataMap = {}
            self.itemView.DeleteAllItems()
            #not clear allItemDataMap
                
            for aKey, aItem in self.itemView.allItemDataMap.items():
                itemTagStr = aItem[TAG_COL_IDX]
                itemTags = itemTagStr.split(';')
                if tag in itemTags:
                    #if not aKey in self.itemView.itemDataMap.keys():
                    self.itemView.showRow(aKey)
                        
        self.winlog(len(self.itemView.itemDataMap))

    def keyEvt(self, event):
        sender = event.GetEventObject()
        key = event.GetKeyCode()
        if self.pathView == sender:
            if wx.WXK_DELETE == key:
                self.pathDel()
            elif wx.WXK_F2 == event.GetKeyCode():
                self.pathSync_F2()
            elif wx.WXK_F3 == event.GetKeyCode():#clear all
                self.pathClear_F3()
        elif self.itemView == sender:
            if wx.WXK_DELETE == key:
                self.itemDel()
            elif wx.WXK_F7 == key:
                self.itemOpenDir_F7()
            elif wx.WXK_F8 == key:
                self.itemOpen_F8()
            elif wx.WXK_F5 == key:
                self.itemSelectAll_F5()
            elif wx.WXK_F6 == key:
                self.itemSortRev_F6()
            elif wx.WXK_F9 == event.GetKeyCode():
                self.itemSetTag_F9()
            elif wx.WXK_F11 == event.GetKeyCode():
                self.itemNewTag_F11()
            elif wx.WXK_F12 == event.GetKeyCode():
                self.itemDelTag_F12()
            elif wx.WXK_F10 == event.GetKeyCode():
                self.itemAutoTag_F10()
            elif wx.WXK_F4 == event.GetKeyCode():#multi set cell
                self.itemBatchEdit_F4()
    
    def repaintTagView(self):
        self.model.buildTagsHtmlStr()
        self.tagView.SetPage(self.model.tagHtmlStr)
        ui_utils.addFullExpandChildComponent(self.tagView)
        
    def _listBeginEdit(self, event):#disable edit: path, tags
        if READONLY == self.itemView.columns[event.Column][3]:
            event.Veto()#Readonly
        else:
            self.oldval = event.Text
            #ui_utils.log('edit item')
    def _readonlyCell(self, event):
        event.Veto()
        
    def evt_1(self):
        print '========'
        for k in sorted(self.model.tagdata.keys()):
            print '%s,%d'%(k,self.model.tagdata[k])
    def evt_3(self):
        print '========'
        for i in range(self.itemView.GetItemCount()):
            print self.itemView.getText(i, 1)
        print '========'
        for i in range(self.itemView.GetItemCount()):
            print self.itemView.getText(i, 0)
    def evt_2(self):
        for i in self.itemView.getSelectedRowId():
            p = self.itemView.getText(i, PATH_COL_IDX)
            size = 0L
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
            elif os.path.isfile(p):
                size = os.path.getsize(p)
            size = '{:,}'.format(size).replace(',',';')
                
            oldComment = self.itemView.getText(i, COMMENT_COL_IDX)
            self.itemView.modRow(i, COMMENT_COL_IDX, '{%s}%s'%(size,oldComment), True)
            
        self.model.saveItem()            
        
def makeMainWin():
    mainWin = MainWin()
    
    model = Model()
    mainWin.setToolbarDefaultFilter(model.defaultFilters)
        
    view1 = SplitView(mainWin.getViewPort())
    view2 = HtmlView(view1.p1)
    view3 = ListView(view1.p2, (('Pathes', 200, wx.LIST_FORMAT_LEFT, 'ro'), ))    
    view4 = ListView(view1.p3, model.itemcolumns)
    
    evtHandler = EventHandler(view2, view3, view4, model, mainWin.log)
    view3.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.keyEvt)
    view4.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.keyEvt)
    
    view4.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.itemEdit)
    FileDropTarget(view3).registerPathAdd(evtHandler.pathAdd_Drop)
    mainWin.registerSearcher(evtHandler.itemFilterByInput)
    view2.registerTagClick(evtHandler.itemFilterByTag)
    
    view3.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler._readonlyCell)
    view4.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler._listBeginEdit)
    
    mainWin.BindToolbarEvent(20, evtHandler.pathSync_F2)
    mainWin.BindToolbarEvent(30, evtHandler.pathClear_F3)
    mainWin.BindToolbarEvent(40, evtHandler.itemBatchEdit_F4)
    mainWin.BindToolbarEvent(50, evtHandler.itemSelectAll_F5)
    mainWin.BindToolbarEvent(60, evtHandler.itemSortRev_F6)
    mainWin.BindToolbarEvent(70, evtHandler.itemOpenDir_F7)
    mainWin.BindToolbarEvent(80, evtHandler.itemOpen_F8)
    mainWin.BindToolbarEvent(90, evtHandler.itemSetTag_F9)
    mainWin.BindToolbarEvent(100, evtHandler.itemAutoTag_F10)
    mainWin.BindToolbarEvent(110, evtHandler.itemNewTag_F11)
    mainWin.BindToolbarEvent(120, evtHandler.itemDelTag_F12)
    
    mainWin.BindToolbarEvent(910, evtHandler.evt_1)
    mainWin.BindToolbarEvent(920, evtHandler.evt_2)
    mainWin.BindToolbarEvent(930, evtHandler.evt_3)
    
    for key, val in model.itemdata.items():
        view4.addRow(val)
    for key, val in model.pathdata.items():
        view3.addRow(val)
    
    evtHandler.repaintTagView()
    ui_utils.addFullExpandChildComponent(view3)
    ui_utils.addFullExpandChildComponent(view4)
    
    mainWin.log(len(view4.itemDataMap))
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
        ADD_ITEM_RECURSION = '_%s%s' % (sys.argv[1], ADD_ITEM_RECURSION[1:])
        ADD_ALL_RECURSION = '_%s%s' % (sys.argv[1], ADD_ALL_RECURSION[1:])
    makeMainWin()
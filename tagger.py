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

#--------BEGIG default config
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

#--------BEGIN ui utils
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
    def addFullExpandChildComponent(parent, child):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(child, 1, wx.EXPAND)
        parent.SetSizer(sizer)
        parent.SetAutoLayout(True)
        
        child.SetSize(parent.GetSize())
        child.SetBackgroundColour(parent.GetBackgroundColour())
        
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
        self._initColumns()
        
        #wx.ListCtrl.EnableAlternateRowColours(self, True)
        #print dir(super(wx.ListCtrl, self))#.EnableAlternateRowColours(True)
        
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
            
    def _initColumns(self):
        i = 0
        for col in self.columns:
            self.InsertColumn(i, col[0], col[2])#name, align
            self.SetColumnWidth(i, col[1])#width
            i += 1
    
    def refreshData(self, listItemDict):
        '''
        #for select statue after refresh
        selIdxes = []
        for i in range(self.GetItemCount()):
            if self.IsSelected(i):
                selIdxes.append(self.GetItemData(i))
        '''
        self.itemDataMap = listItemDict
        
        '''
        self.DeleteAllItems()
        for key, data in listItemDict.items():
            index = self.InsertStringItem(sys.maxint, data[0])
            for i in range(1, len(data)):
                self.SetStringItem(index, i, data[i])
            self.SetItemData(index, key)
        '''
        rowIdx = self.GetItemCount() - 1
        while rowIdx >= 0:
            rowData = self.GetItemData(rowIdx)
            if not rowData in listItemDict.keys():
                self.DeleteItem(rowIdx)
            else:
                for colIdx in range(0, len(listItemDict[rowData])):
                    if not listItemDict[rowData][colIdx] == self.GetItem(rowIdx, colIdx).GetText():
                        self.SetStringItem(rowIdx, colIdx, listItemDict[rowData][colIdx])
                        
            rowIdx -= 1
            
        for id in listItemDict.keys():
            found = False
            for rowIdx in range(0, self.GetItemCount()):
                if self.GetItemData(rowIdx) == id:
                    found = True
                    break
            if not found:
                index = self.InsertStringItem(sys.maxint, listItemDict[id][0])
                for i in range(1, len(listItemDict[id])):
                    self.SetStringItem(index, i, listItemDict[id][i])
                self.SetItemData(index, id)
            '''
            #for select statue after refresh
            if key in selIdxes:
                self.Select(index)
            '''
            
        ui_utils.addFullExpandChildComponent(self.Parent, self)
    
    def readonlyCell(self, event):#disable edit: path, tags
        event.Veto()#Readonly

class TestSearchCtrl(wx.SearchCtrl):
    maxSearches = 50
    
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
            del self.searches[0]
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
#========                   
                   
#--------BEGIN Model_Serializable
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
               
#--------BEGIN Model
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
        self.displayItemData = {}#displayed in Item List View
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
        
        self.refreshObj = {}

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
        self._buildTagsHtmlStr()
    def _buildTagsHtmlStr(self):
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
            
        self.displayItemData = self.itemdata       
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
                
    def saveItem(self, comfirm=False):
        io.save(self._tostrsItem(), ITEM_CONFIG_F_NAME, comfirm)
    def savePath(self, comfirm=False):
        io.save(self._tostrsPath(), PATH_CONFIG_F_NAME, comfirm)
    def _tostrsItem(self):
        ret = [self.itemColumnStr]
        for i in self.itemdata.values():
            ret.append(','.join(i))
        return ret
    def _tostrsPath(self):
        return [p[0] for p in self.pathdata.values()]
                
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
    def _hasTag(self, rowKey, aTag):
        itemInAll = self.itemdata[rowKey]
        itemTagStr = itemInAll[TAG_COL_IDX]
        itemTags = itemTagStr.split(';')
        return aTag in itemTags
                
    def buildLogStr(self):
        return self.filterLogTemplate % (len(self.displayItemData), self.filterTag, ' and '.join(self.filterStrs))
        
    def clearAll(self):
        self.tagdata = {}
        self.itemdata = {}
        self.displayItemData = {}
        self.pathdata = {}
        
    def refreshAll(self):
        self._buildTagsHtmlStr()
        self.refreshObj[TAG_CONFIG_F_NAME].refreshData(self.tagHtmlStr)
        self.refreshObj[PATH_CONFIG_F_NAME].refreshData(self.pathdata)
        self.refreshObj[ITEM_CONFIG_F_NAME].refreshData(self.displayItemData)
    
    def filterItemByTag(self, tag):
        if ALL_TAG == tag:
            self.displayItemData = self.itemdata
        else:
            self.displayItemData = {}
            for key in self.itemdata.keys():
                if self._hasTag(key, tag):
                    self.displayItemData[key] = self.itemdata[key]
    def filterItemByFormular(self, text):
        ui_utils.log('filter by formular: %s'%text)
        
        if '' == text.strip():
            self.displayItemData = self.itemdata
        else:
            dispitem = {}
            for id, row in self.displayItemData.items():
                if eval(text):
                    dispitem[id] = self.displayItemData[id]
                        
            self.displayItemData = dispitem
        
    def dowithOneTag4OneItem(self, rowKey, newTag, isAdd):#used by tagSet and pathSync
        if ALL_TAG == newTag:#ALL can't be set as a tag
            ui_utils.warn('ALL can\' be set as a tag')
            return
            
        itemInAll = self.itemdata[rowKey]
        #itemInDisplay = self.displayItemData[rowKey]
        itemTagStr = itemInAll[TAG_COL_IDX]
        itemTags = itemTagStr.split(';')
        if isAdd:
            if not newTag in itemTags:
                #delete all tags when set DEL
                if SYS_TAG_DEL == newTag:
                    for otherTag in itemTags:
                        self._decTag(otherTag)
                    itemInAll[TAG_COL_IDX] = ''
                    
                if len(itemInAll[TAG_COL_IDX]) > 0:
                    itemTags.append(newTag)
                    itemInAll[TAG_COL_IDX] = ';'.join(sorted(itemTags))
                else:
                    itemInAll[TAG_COL_IDX] = newTag
                #itemInDisplay[TAG_COL_IDX] = itemInAll[TAG_COL_IDX]
                self._incTag(newTag)
        else:
            if newTag in itemTags:
                itemTags.remove(newTag)
                if len(itemTags) > 0:
                    itemInAll[TAG_COL_IDX] = ';'.join(sorted(itemTags))
                else:
                    itemInAll[TAG_COL_IDX] = ''
                self._decTag(newTag)

    def autoTagEvt(self, filenames):#[(file,key),]
        for file, rowKey in filenames:
            _ext = os.path.splitext(file)[1].lower()
            if not '' == _ext:
                if _ext in self.ext.keys():
                    self.dowithOneTag4OneItem(rowKey, self.ext[_ext], True)
                    self.dowithOneTag4OneItem(rowKey, _ext, False)#rmv tag if defined before
                else:
                    self.dowithOneTag4OneItem(rowKey, _ext, True)
    def delItemByEvt(self, filenames):#[(file,key),]
        for file in filenames:
            rowid = file[1]
            itemTags = self.itemdata[rowid][TAG_COL_IDX].split(';')
            for itemTag in itemTags:
                self._decTag(itemTag)
            self.itemdata.pop(rowid)            
    def delPathByEvt(self, filenames):#only rmv Path, not care items
        for file in filenames:
            self.pathdata.pop(file[1])
    def itemSetTagEvt(self, rows, *args):#[(file,key),], tag list, rev
        for newTag in args[0]:
            for aRow in rows:
                rowKey = aRow[1]
                if 2 == len(args) and args[1]:#Revert Tag
                    _tagSet = self._hasTag(rowKey, newTag)
                    if _tagSet: self.dowithOneTag4OneItem(rowKey, newTag, False)#rmv tag
                    else: self.dowithOneTag4OneItem(rowKey, newTag, True)#add tag
                else:#default is False
                    if '+' == newTag[0]:
                        self.dowithOneTag4OneItem(rowKey, newTag[1:], True)#add tag
                    elif '-' == newTag[0]:
                        self.dowithOneTag4OneItem(rowKey, newTag[1:], False)#rmv tag
    def itemMultiSetEvt(self, rows, *args):#[(file,key),], cell value
        setNewValue = args[0]#row[col] = u'xxx'
        #print setNewValue
        for aRow in rows:
            row = self.itemdata[aRow[1]]
            #self.itemdata[aRow[1]][colIdx] = newVal
            exec(setNewValue)#use exec, not eval
            #print 'done'
    
    def _addPathOnly(self, newpath):#called by addPath. not care items
        if not os.path.sep == newpath[-1]:
            newpath = '%s%s'%(newpath, os.path.sep)#fix bug when a path aaa and another path aaa-bbb, rmv aaa-bbb, it's children will not be rmv
            
        found = False
        for p in self.pathdata.values():
            #if newpath.startswith(p[0]):#fix bug: if upper path added, child path can't be added anymore
            if newpath == p[0]:#do not change. because there is difference under NO recursion mode
                found = True
                break
                
        if found:
            #ui_utils.warn('%s already exists'%newpath)
            return False
        else:
            newid = self._newid(self.pathdata)
            self.pathdata[newid] = (newpath, )
            #ui_utils.log('model add %s, pathdata count is %d'%(newpath,len(self.pathdata.keys())))
            return True
    def _addItem(self, filepath, filename):#called by addPath or syncPath, NO LOG when already exists
        for i_blackrule in self.blacklist:
            if eval(i_blackrule):
                ui_utils.warn('%s matches %s'%(filepath, i_blackrule))
                return
                
        found = False
        for f in self.itemdata.values():
            if filepath == f[1]:
                found = True
                break
                
        if not found:
            newid = self._newid(self.itemdata)
                
            if os.path.isfile(filepath):
                filename = os.path.splitext(filename)[0]#only file name, without ext
            #self.itemdata[newid] = [filename,filepath,ui_utils.today(),SYS_TAG_NEW,'']
            self._initOneItemRow(newid, [filename,filepath,ui_utils.today(),SYS_TAG_NEW])#fix bug: add item with less field
            self.displayItemData[newid] = self.itemdata[newid]
            
            self._incTag(SYS_TAG_NEW)
            return True
            #ui_utils.log('Item %s added'%filepath)
        else:
            return False
            
    def addPathByEvt(self, filenames):#[file,]
        added = False
        for file in filenames:
            if os.path.isdir(file):#path exists in Disk
                thispathadded = self._addPathOnly(file)#path added
                if thispathadded:
                    added = True
                    for f in ui_utils.getSubFiles(file):
                        try:
                            self._addItem(f[0], f[1])#path, filename
                        except Exception,e:#UnicodeDecodeError
                            ui_utils.error(os.path.join(f[0], f[1]))
                            raise e
            
        return added

    def syncPath(self):#soft remove item if it's parent path is not exists or file not exists on Disk
        modified = False
        pathlist = [p[0] for p in self.pathdata.values()]#all pathes
        for k, i in self.itemdata.items():
            if not SYS_TAG_RMV in i[TAG_COL_IDX].split(';'):
                _inPath = False
                for p in pathlist:#do with items not under path
                    if p in i[PATH_COL_IDX]:
                        _inPath = True
                        break
                        
                if not _inPath:
                    self.dowithOneTag4OneItem(k, SYS_TAG_RMV, True)#soft delete item
                    modified = True
                elif not os.path.exists(i[PATH_COL_IDX]):#do with file not exists
                    self.dowithOneTag4OneItem(k, SYS_TAG_RMV, True)#soft delete item
                    modified = True
                    
        for p in pathlist:
            for f in ui_utils.getSubFiles(p):
                if self._addItem(f[0], f[1]):
                    modified = True
                
        return modified            
            
#--------BEGIN Controllor
class EventHandler(object):
    def __init__(self, model, winlog, modelKeyColIdx=0):
        self.model = model
        self.winlog = winlog
        self.modelKeyColIdx = modelKeyColIdx
        
    def tagFilter(self, tagStr):#select tag
        try:
            tag = tagStr[1:-1]
            tag = tag.split(':')[0]
            self.model.filterItemByTag(tag)
            
            self.model.refreshAll()
            #self.winlog('filter item by tag done')
            self.model.filterTag = tag
            self.model.filterStrs = []
            self.winlog(self.model.buildLogStr())
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def formularFilter(self, text):
        try:
            self.model.filterItemByFormular(text)
            
            self.model.refreshAll()
            #self.winlog('filter item by formular done')
            
            self.model.filterStrs.append(text)
            self.winlog(self.model.buildLogStr())
        except Exception,e:
            self.winlog(str(e), True)
            raise e
    def selAllImpl(self):
        for i in range(self.model.refreshObj[ITEM_CONFIG_F_NAME].GetItemCount()):
            self.model.refreshObj[ITEM_CONFIG_F_NAME].Select(i)
    def revSortImpl(self):
        self.model.refreshObj[ITEM_CONFIG_F_NAME].onRevSort(PATH_COL_IDX)
            
    def itemOpen(self):
        try:
            os.startfile(\
                self.model.itemdata[self.model.refreshObj[ITEM_CONFIG_F_NAME].GetItemData(\
                self.model.refreshObj[ITEM_CONFIG_F_NAME].GetFirstSelected())][PATH_COL_IDX])
            #self.winlog('open item done')
        except Exception,e:
            self.winlog(str(e), True)
            raise e
    def itemOpenDir(self):
        try:
            os.startfile(\
                os.path.dirname(\
                self.model.itemdata[self.model.refreshObj[ITEM_CONFIG_F_NAME].GetItemData(\
                self.model.refreshObj[ITEM_CONFIG_F_NAME].GetFirstSelected())][PATH_COL_IDX]))
            #self.winlog('open item dir done')
        except Exception,e:
            self.winlog(str(e), True)
            raise e
    def clrImpl(self):#do not save
        _dlg = wx.MessageDialog(None, 'ALL DATA WILL BE CLEARED. but no data saved until new data added', '!!!', wx.YES_NO | wx.ICON_EXCLAMATION)
        if wx.ID_YES == _dlg.ShowModal():
            self.model.clearAll()
            self.model.refreshAll()
        _dlg.Destroy()
    
    def pathDel(self):
        try:
            self._dealRows(self.model.refreshObj[PATH_CONFIG_F_NAME], self.model.delPathByEvt)
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def itemDel(self):
        try:
            self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.delItemByEvt)
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def autoTag(self):
        try:
            self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.autoTagEvt)
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def itemSetTag(self):
        try:
            _dlg = wx.TextEntryDialog(None, "'+' means add, '-' means del, split tags by ';'", 'Set Tag(s)')
            if _dlg.ShowModal() == wx.ID_OK:
                newTags = [x.strip() for x in _dlg.GetValue().split(';')]
                self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.itemSetTagEvt, newTags)
            _dlg.Destroy()
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def _dealRows(self, list, dealImpl, *args):
        fileAttr = []
        selectedRow = list.GetFirstSelected()
        while not -1 == selectedRow:
            selKey = list.GetItem(selectedRow, self.modelKeyColIdx).GetText()
            selIdx = list.GetItemData(selectedRow)
            fileAttr.append((selKey, selIdx))#Key(Path), ItemData not row Index
            selectedRow = list.GetNextSelected(selectedRow)
            
        dealImpl(fileAttr, *args)
        
        self.model.refreshAll()
        self.model.savePath()
        self.model.saveItem()
    def setNewTag(self):
        try:
            self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.itemSetTagEvt, (SYS_TAG_NEW,), True)
            self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.itemSetTagEvt, ('-%s'%SYS_TAG_DEL,))
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def setDelTag(self):
        try:
            self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.itemSetTagEvt, (SYS_TAG_DEL,), True)
            #self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.itemSetTagEvt, ('-%s'%SYS_TAG_NEW,))
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def batSetImpl(self):
        try:
            _dlg = wx.TextEntryDialog(None, "row[?] = u'xxx'", 'Set Cells for Multi Rows')
            if _dlg.ShowModal() == wx.ID_OK:
                setNewValue = _dlg.GetValue()
                self._dealRows(self.model.refreshObj[ITEM_CONFIG_F_NAME], self.model.itemMultiSetEvt, setNewValue)
            _dlg.Destroy()
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def pathAdd(self, x, y, filenames):#add path
        try:
            added = self.model.addPathByEvt(filenames)
            if added:
                self.model.refreshAll()
                self.model.saveItem()
                self.model.savePath()
                #self.winlog('add path done')
        except Exception, e:
            self.winlog(str(e), True)
            for f in filenames:
                ui_utils.error(f)
            raise e
            
    def pathSync(self):
        try:
            modified = self.model.syncPath()
            
            if modified:
                self.model.refreshAll()
                self.model.saveItem()
                #self.winlog('refresh path done')
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def itemSet(self, event):#edit
        try:
            if not self.oldval == event.Text:
                #event.Allow()
                self.model.itemdata[self.model.refreshObj[ITEM_CONFIG_F_NAME].GetItemData(\
                    self.model.refreshObj[ITEM_CONFIG_F_NAME].GetFirstSelected())][event.Column] = event.Text.replace(',',';')#refresh automatically
                    #fix csv bug when input ,
                self.model.saveItem()
                #self.winlog('edit cell done')
            del self.oldval
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    def _listBeginEdit(self, event):#disable edit: path, tags
        try:
            if READONLY == self.model.refreshObj[ITEM_CONFIG_F_NAME].columns[event.Column][3]:
                event.Veto()#Readonly
            else:
                self.oldval = event.Text
                #ui_utils.log('edit item')
        except Exception, e:
            winlog(str(e), True)
        
    def pathListKeyDown(self, event):
        if wx.WXK_DELETE == event.GetKeyCode():
            self.pathDel()
        elif wx.WXK_F2 == event.GetKeyCode():
            self.pathSync()
        elif wx.WXK_F3 == event.GetKeyCode():#clear all
            self.clrImpl()
    def itemListKeyDown(self, event):
        if wx.WXK_DELETE == event.GetKeyCode():
            self.itemDel()
        elif wx.WXK_F9 == event.GetKeyCode():
            self.itemSetTag()
        elif wx.WXK_F8 == event.GetKeyCode():
            self.itemOpen()
        elif wx.WXK_F7 == event.GetKeyCode():
            self.itemOpenDir()
        elif wx.WXK_F5 == event.GetKeyCode():#select all
            self.selAllImpl()
        elif wx.WXK_F6 == event.GetKeyCode():#user define sorter
            #self.winlog('sort by path rev done')
            self.revSortImpl()
        elif wx.WXK_F4 == event.GetKeyCode():#multi set cell
            self.batSetImpl()
        elif wx.WXK_F11 == event.GetKeyCode():
            self.setNewTag()
        elif wx.WXK_F12 == event.GetKeyCode():
            self.setDelTag()
        elif wx.WXK_F10 == event.GetKeyCode():
            self.autoTag()
            
        
class FileDropTarget(wx.FileDropTarget):
    def __init__(self, window, model, winlog):
        wx.FileDropTarget.__init__(self)  
        window.SetDropTarget(self)
        self.dropFile = EventHandler(model, winlog).pathAdd
    def OnDropFiles(self, x, y, filenames):
        self.dropFile(x, y, filenames)            
#--------BEGIN UI
def makeMainWin():
    mainWin = MainWin()
    model = Model()
    mainWin.setToolbarDefaultFilter(model.defaultFilters)
    mainWin.registerSearcher(EventHandler(model, mainWin.log).formularFilter)
    
    view1 = SplitView(mainWin.getViewPort())
    
    view2 = HtmlView(view1.p1, EventHandler(model, mainWin.log).tagFilter)
    model.refreshObj[TAG_CONFIG_F_NAME] = view2#view2.refreshData(model.tagHtmlStr)
    
    view3 = ListView(view1.p2, (('Pathes', 200, wx.LIST_FORMAT_LEFT, 'ro'), ))
    evtHandler = EventHandler(model, mainWin.log)
    view3.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, view3.readonlyCell)#must set for readonly
    #view3.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.listEndEdit)
    view3.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.pathListKeyDown)
    FileDropTarget(view3, model, mainWin.log)
    model.refreshObj[PATH_CONFIG_F_NAME] = view3#view3.refreshData(model.getPathes())
    mainWin.BindToolbarEvent(20, evtHandler.pathSync)
    mainWin.BindToolbarEvent(30, evtHandler.clrImpl)
    mainWin.BindToolbarEvent(40, evtHandler.batSetImpl)
    
    view4 = ListView(view1.p3, model.itemcolumns)
    evtHandler = EventHandler(model, mainWin.log, PATH_COL_IDX)#define key column
    view4.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler._listBeginEdit)
    view4.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.itemSet)
    view4.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.itemListKeyDown)
    model.refreshObj[ITEM_CONFIG_F_NAME] = view4#view4.refreshData(model.displayItemData)
    mainWin.BindToolbarEvent(50, evtHandler.selAllImpl)
    mainWin.BindToolbarEvent(60, evtHandler.revSortImpl)
    mainWin.BindToolbarEvent(70, evtHandler.itemOpenDir)
    mainWin.BindToolbarEvent(80, evtHandler.itemOpen)
    mainWin.BindToolbarEvent(90, evtHandler.itemSetTag)
    mainWin.BindToolbarEvent(100, evtHandler.autoTag)
    mainWin.BindToolbarEvent(110, evtHandler.setNewTag)
    mainWin.BindToolbarEvent(120, evtHandler.setDelTag)
    #view4.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, evtHandler.itemOpen)#change to F8
            
    model.refreshAll()
    mainWin.log('show me done')

    mainWin.MainLoop()
    












          
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
    if 2 == len(sys.argv):
        #global PATH_CONFIG_F_NAME, ITEM_CONFIG_F_NAME, EXT_CONFIG_F_NAME, BLACK_LIST_F_NAME, FILTER_CONFIG_F_NAME
        PATH_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], PATH_CONFIG_F_NAME[1:])
        ITEM_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], ITEM_CONFIG_F_NAME[1:])
        EXT_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], EXT_CONFIG_F_NAME[1:])
        BLACK_LIST_F_NAME = '_%s%s' % (sys.argv[1], BLACK_LIST_F_NAME[1:])
        FILTER_CONFIG_F_NAME = '_%s%s' % (sys.argv[1], FILTER_CONFIG_F_NAME[1:])
        ITEM_CONFIG_LINK = '_%s%s' % (sys.argv[1], ITEM_CONFIG_LINK[1:])
    makeMainWin()
    
#How to pydoc
#c:\python27\python -m pydoc tagger
#NOTE: tagger without .py
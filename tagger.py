'''
^ name: tag tool
^ author: tillfall(tillfall@126.com)
^ version: 1.3
^ create: 2016-02-21
^ release: 2016-02-26
^ platform: py2.7 & wx3.0

^ bug: RuntimeWarning when delItem--syncPath--sortByTag
^ req: show item id in list

^ done in v1.3: auto tag by ext
^ done in v1.2: find by formular
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

#--------BEGIG default config
ADD_ITEM_RECURSION = False

PATH_CONFIG_F_NAME = '_pathes.txt'
TAG_CONFIG_F_NAME = '_tags.htm'
ITEM_CONFIG_F_NAME = '_items.txt'

READONLY = 'ro'
SYS_TAG_NEW = 'sys-new'
SYS_TAG_DEL = 'sys-del'
ALL_TAG ='ALL'

TAG_COL_IDX = 3
PATH_COL_IDX = 1

HELP = 'F2:SetTag, F5:SyncPath/AutoTag, F11:NEW, F12:DEL, F8:Open, F6:SelectAll'

#--------BEGIN ui utils
class ui_utils(object):
    _log_inited = False
    @staticmethod
    def today():
        return datetime.datetime.now().strftime('%Y-%m-%d')
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
        frame = wx.Frame(None, -1, "tagger  --  [%s]"%HELP, pos=(50,50), size=(800,600),
                        style=wx.DEFAULT_FRAME_STYLE, name="tagger")
        self.sb = frame.CreateStatusBar()
        #self.sb.SetFieldsCount(2)
        
        self.tb = frame.CreateToolBar(( wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT))
        #self.tb.AddStretchableSpace()#right align
        search = TestSearchCtrl(self.tb, size=(600, -1), doSearch=self._search)
        search.SetDescriptiveText('example: row[?] == "" or "" in row[?]')
        self.tb.AddControl(search)
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
    def show(self):
        self.MainLoop()
        
    def registerSearcher(self, searcher):
        self._searchImpl = searcher
    def _search(self, text):
        self._searchImpl(text)
        
    def log(self, text, onErr=False):
        if not onErr:
            self.sb.PushStatusText(text)
        else:
            _dlg = wx.MessageDialog(None, text, 'ERROR', wx.OK)
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
        #for select statue after refresh
        selIdxes = []
        for i in range(self.GetItemCount()):
            if self.IsSelected(i):
                selIdxes.append(self.GetItemData(i))
        
        self.itemDataMap = listItemDict
        
        self.DeleteAllItems()
        for key, data in listItemDict.items():
            index = self.InsertStringItem(sys.maxint, data[0])
            for i in range(1, len(data)):
                self.SetStringItem(index, i, data[i])
            self.SetItemData(index, key)
            
            #for select statue after refresh
            if key in selIdxes:
                self.Select(index)
        ui_utils.addFullExpandChildComponent(self.Parent, self)
        
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

    def OnTextEntered(self, evt):
        text = self.GetValue()
        
        self.doSearch(text)
        self.searches.append(text)
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
            menu.Append(1+idx, txt)
        return menu        
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
    def save(lst, fname):
        file = codecs.open(fname, 'w', 'gb2312')
        for l in lst:
            file.write('%s\n'%l)
        file.close()
        ui_utils.log('save %s, %d lines' % (fname, len(lst)))
               
#--------BEGIN Model
class Model(object):
    def __init__(self):
        self.tagdata = {}#{tag1:count,}
        self.tagHtmlStr = None
        self.tagHeaderStr = None
        self.tagFooterStr = None
        self.tagTemplate = '<tag>[%s]</tag>'
        self.tagBodyTemplate = '<data>%s</data>'

        self.pathdata = {}#{1:(path1,),}
        
        self.itemdata = {}#{1:(col1,col2,col3,),}
        #all Items to be saved
        self.displayItemData = {}#displayed in Item List View
        self.itemcolumns = []#[[col1,width,align,ro,],]
        self.itemColumnStr = None
        
        #self.tagSizeTemplate = '<font size=%s>%s</font>'
        #self.tagColorTemplate = '<font color=%s>%s</font>'

        #self.tagColorDefine = {'sys-%s':'gray', }
        #self.tagSizeDefine = {(100,sys.maxint):'+5', (50,99):'+4', (1,10):'-2', (11,49):'+0'}
        
        self._initPath()
        self._initItemsAndColumn()
        self._initTagHtml()
        
        self.refreshObj = {}
        
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
            for key, item in self.itemdata.items():
                itemTags = item[TAG_COL_IDX].split(';')
                if tag in itemTags:
                    self.displayItemData[key] = item
    
    def hasTag(self, rowKey, aTag):
        itemInAll = self.itemdata[rowKey]
        itemTagStr = itemInAll[TAG_COL_IDX]
        itemTags = itemTagStr.split(';')
        return aTag in itemTags
        
    def addTag4Item(self, rowKey, newTag):#only for tag set
        self._dowithTag4Item(rowKey, newTag, True)
    def rmvTag4Item(self, rowKey, newTag):#only for tag set
        self._dowithTag4Item(rowKey, newTag, False)
    def _dowithTag4Item(self, rowKey, newTag, isAdd):#used by tagSet and pathSync
        itemInAll = self.itemdata[rowKey]
        #itemInDisplay = self.displayItemData[rowKey]
        itemTagStr = itemInAll[TAG_COL_IDX]
        itemTags = itemTagStr.split(';')
        if isAdd:
            if newTag in itemTags:
                ui_utils.warn('add tag fail, %s already set for %d'%(newTag, rowKey))
            else:
                if len(itemInAll[TAG_COL_IDX]) > 0:
                    itemTags.append(newTag)
                    itemInAll[TAG_COL_IDX] = ';'.join(sorted(itemTags))
                else:
                    itemInAll[TAG_COL_IDX] = newTag
                #itemInDisplay[TAG_COL_IDX] = itemInAll[TAG_COL_IDX]
                if newTag in self.tagdata.keys():
                    self.tagdata[newTag] += 1
                else:
                    self.tagdata[newTag] = 1
        else:
            if newTag in itemTags:
                itemTags.remove(newTag)
                if len(itemTags) > 0:
                    itemInAll[TAG_COL_IDX] = ';'.join(sorted(itemTags))
                else:
                    itemInAll[TAG_COL_IDX] = ''
                if not newTag in self.tagdata.keys():
                    ui_utils.warn('tag %s not exists'%newTag)
                elif 1 == self.tagdata[newTag]:
                    self.tagdata.pop(newTag)
                else:
                    self.tagdata[newTag] -= 1
            else:
                ui_utils.warn('rmv tag fail, %s not set for %d'%(newTag, rowKey))
                
    def saveItem(self):
        io.save(self._tostrsItem(), ITEM_CONFIG_F_NAME)
    def savePath(self):
        io.save(self._tostrsPath(), PATH_CONFIG_F_NAME)
    def _tostrsItem(self):
        ret = [self.itemColumnStr]
        for i in self.itemdata.values():
            ret.append(','.join(i))
        return ret
    def _tostrsPath(self):
        return [p[0] for p in self.pathdata.values()]
         
    def _initPath(self):
        idx = 0
        for line in io.load(PATH_CONFIG_F_NAME):
            self.pathdata[idx] = (line.strip(), )
            idx += 1
    def _initTagHtml(self):
        self.tagHtmlStr = '\n'.join(io.load(TAG_CONFIG_F_NAME))
        
        ss = re.split(self.tagBodyTemplate%'(.|\n)+', self.tagHtmlStr, flags=re.IGNORECASE)#ignore \n
        self.tagHeaderStr = ss[0]
        self.tagFooterStr = ss[2]
        
        #content inited by items
        self._buildTagsHtmlStr()
    def _buildTagsHtmlStr(self):
        _tags = []
        for aTag, aCount in self.tagdata.items():
            _tags.append(self.tagTemplate%('%s:%d'%(aTag, aCount)))
        tagStr = '\n'.join(_tags)
        
        self.tagHtmlStr = '%s%s%s' % (self.tagHeaderStr, self.tagBodyTemplate%tagStr, self.tagFooterStr % len(self.itemdata))
    def _initItemsAndColumn(self):
        lines = io.load(ITEM_CONFIG_F_NAME)
        
        self.itemColumnStr = lines[0]
        self._initColumns(lines[0])
        
        idx = 0
        for line in lines[1:]:
            linestr = line.split(',')
            self.itemdata[idx] = linestr
            
            tagstr = linestr[TAG_COL_IDX]#tag
            if len(tagstr) > 0:
                for aTag in tagstr.split(';'):
                    self._incTag(aTag)
            idx += 1
            
        self.displayItemData = self.itemdata
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
            ui_utils.warn('empty tag inc')
            return
        if aTag in self.tagdata.keys():
            self.tagdata[aTag] += 1
        else:
            self.tagdata[aTag] = 1
    def _decTag(self, aTag):
        if '' == aTag:
            ui_utils.warn('empty tag dec')
            return
        if aTag in self.tagdata.keys():
            self.tagdata[aTag] -= 1
            if 0 == self.tagdata[aTag]:
                self.tagdata.pop(aTag)
        else:
            ui_utils.warn('dec tag when not exists')
    
    def _newid(self, dict):
        if {} == dict:
            return 1
        else:
            return max(dict.keys()) + 1
    
    def _getChildren(self, rootpath):
        ret = []
        if ADD_ITEM_RECURSION:
            for root, dirs, files in os.walk(rootpath):
                for file in files:#do not include folder
                    ret.append((os.path.join(root, file), file))
        else:
            for file in os.listdir(rootpath):
                ret.append((os.path.join(rootpath, file), file))
        return ret
    
    def syncPath(self):
        pathlist = [p[0] for p in self.pathdata.values()]#all pathes
        for k, i in self.itemdata.items():
            if not SYS_TAG_DEL in i[TAG_COL_IDX].split(';'):
                for p in pathlist:#do with items not under path
                    if not p in i[PATH_COL_IDX]:
                        self._dowithTag4Item(k, SYS_TAG_DEL, True)#soft delete item
                        break
                if not os.path.exists(i[PATH_COL_IDX]):#do with file not exists
                    self._dowithTag4Item(k, SYS_TAG_DEL, True)#soft delete item
                    
        for p in pathlist:
            for f in self._getChildren(p):
                self._addItem(f[0], f[1])
                
        return True
    def _addItem(self, filepath, filename):#called by addPath or syncPath, NO LOG when already exists
        found = self._findItem(filepath)
        if not found:
            newid = self._newid(self.itemdata)
                
            if os.path.isfile(filepath):
                filename = os.path.splitext(filename)[0]#only file name, without ext
            self.itemdata[newid] = [filename,filepath,ui_utils.today(),SYS_TAG_NEW,'']
            self.displayItemData[newid] = self.itemdata[newid]
            
            self._incTag(SYS_TAG_NEW)
            ui_utils.log('Item %s added'%filepath)
    def _findItem(self, file):#only for _addItem
        for f in self.itemdata.values():
            if file == f[1]:
                return True
        return False
        
    def _getIdByPath(self, aPath):
        for id in self.pathdata.keys():
            if aPath == self.pathdata[id][0]:
                return id
        return -1
    def _addPath(self, newpath):#called by addPath. not care items
        id = self._getIdByPath(newpath)
        if not -1 == id:
            ui_utils.warn('%s already exists'%newpath)
            return False
        else:
            newid = self._newid(self.pathdata)
            self.pathdata[newid] = (newpath, )
            ui_utils.log('model add %s, pathdata count is %d'%(newpath,len(self.pathdata.keys())))
            return True
    def addPathByEvt(self, filenames):
        added = False
        for file in filenames:
            if os.path.isdir(file):
                thispathadded = self._addPath(file)
                if thispathadded:
                    added = True
                    for f in self._getChildren(file):
                        self._addItem(f[0], f[1])
                else:
                    ui_utils.warn('add path [%s] failed'%file)
            else:
                ui_utils.warn('add path [%s] failed'%file)
            
        return added
        
    def delPathByEvt(self, filenames):#only rmv Path, not care items
        for file in filenames:
            self._rmvPath(file[1])
    def _rmvPath(self, id):#called by delPathEvt
        self.pathdata.pop(id)

    def delItemByEvt(self, filenames):
        for file in filenames:
            self._rmvItemHard(file[1])
            
    def _rmvItemHard(self, rowid):#called by delItemByEvt
        itemTags = self.itemdata[rowid][TAG_COL_IDX].split(';')
        for itemTag in itemTags:
            self._decTag(itemTag)
        self.itemdata.pop(rowid)
        #self.displayItemData.pop(listKey)
    
    def autoTagEvt(self, filenames):
        for file, rowKey in filenames:
            _ext = os.path.splitext(file)[1]
            if not '' == _ext:
                self.addTag4Item(rowKey, _ext)
            
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
        
        
        
        

            
            
            
            
#--------BEGIN Controllor
class EventHandler(object):
    def __init__(self, sender, model, winlog, modelKeyColIdx=0):
        self.sender = sender
        self.model = model
        self.winlog = winlog
        self.modelKeyColIdx = modelKeyColIdx
        
    def tagFilter(self, tagStr):#select tag
        '''
        ^ [1] filter by click tag
        ^ --------
        '''
        try:
            tag = tagStr[1:-1]
            self.model.filterItemByTag(tag.split(':')[0])
            
            self.model.refreshAll()
        except Exception, e:
            self.winlog(str(e), True)
            raise e
    
    def formularFilter(self, text):
        '''
        ^ [8] filter by formular
        ^ --------
        '''
        try:
            self.model.filterItemByFormular(text)
            
            self.model.refreshAll()
            self.winlog('filter item by formular done')
        except Exception,e:
            self.winlog(str(e), True)
            raise e
            
    def itemOpen(self):
        '''
        ^ [9] open item of path column by right click
        ^ --------
        '''
        try:
            os.startfile(\
                self.model.itemdata[self.sender.GetItemData(self.sender.GetFirstSelected())][PATH_COL_IDX])
            self.winlog('open item done')
        except Exception,e:
            self.winlog(str(e), True)
            raise e
    
    def pathAdd(self, x, y, filenames):#add path
        '''
        ^ [2] drag&drop path to path list
        ^ insert path(es) to tag their sub dirs or files
        ^ --------
        '''
        try:
            added = self.model.addPathByEvt(filenames)
                
            if added:
                self.model.refreshAll()
                self.model.saveItem()
                self.model.savePath()
                self.winlog('add path done')
        except Exception, e:
            self.winlog(str(e), True)
            raise e
            
    def pathDel(self):
        '''
        ^ [3] remove path by click DEL key, multi select is supported
        ^ DO NOT DELETE items under path
        ^ --------
        '''
        try:
            self._delRow(self.model.delPathByEvt, 'rmv path done')
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def pathSync(self):
        '''
        ^ [4] refresh item for all pathes by click F5 key
        ^ if +folder-item: add to item
        ^ if -folder+item: tag item with sys-del
        ^ pathes list must be focused
        ^ --------
        '''
        try:
            modified = self.model.syncPath()
            
            if modified:
                self.model.refreshAll()
                self.model.saveItem()
                self.winlog('refresh path done')
        except Exception, e:
            self.winlog(str(e), True)
            raise e

    def itemDel(self):
        '''
        ^ [5] remove item by click DEL key, multi select is supported
        ^ --------
        '''        
        try:
            self._delRow(self.model.delItemByEvt, 'rmv item done')
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def autoTag(self):
        '''
        ^ [10] remove path by click DEL key, multi select is supported
        ^ DO NOT DELETE items under path
        ^ --------
        '''
        try:
            self._delRow(self.model.autoTagEvt, 'auto tag done')
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def itemSetTag(self):
        '''
        ^ [6] set tags of ITEM by click F2 key, multi select is supported
        ^ '+' means add, '-' means del, split tags by ';'
        ^ --------
        '''
        try:
            _dlg = wx.TextEntryDialog(None, "'+' means add, '-' means del, split tags by ';'", 'Set Tag(s)')
            if _dlg.ShowModal() == wx.ID_OK:
                ui_utils.log(_dlg.GetValue())
                
                for newTag in _dlg.GetValue().split(';'):
                    newTag = newTag.strip()
                    self._itemSetOneTag(newTag)
                    
                self.model.refreshAll()
                self.model.saveItem()
                self.winlog('set tag done')

            _dlg.Destroy()
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def itemSet(self, event):#edit
        '''
        ^ [7] edit grid cell, some column READONLY by 'ro'
        ^ --------
        '''
        try:
            if not self.oldval == event.Text:
                #event.Allow()
                self.model.itemdata[self.sender.GetItemData(self.sender.GetFirstSelected())][event.Column] = event.Text#refresh automatically
                self.model.saveItem()
                self.winlog('edit cell done')
            del self.oldval
        except Exception, e:
            self.winlog(str(e), True)
            raise e
        
    def _delRow(self, delImpl, msg):
        fileAttr = []
        list = self.sender
        selectedRow = list.GetFirstSelected()
        while not -1 == selectedRow:
            selKey = list.GetItem(selectedRow, self.modelKeyColIdx).GetText()
            selIdx = list.GetItemData(selectedRow)
            fileAttr.append((selKey, selIdx))#Key(Path), ItemData not row Index
            selectedRow = list.GetNextSelected(selectedRow)
            
        delImpl(fileAttr)
        
        self.model.refreshAll()
        self.model.savePath()
        self.model.saveItem()
        self.winlog(msg)
    
    def _itemSetOneTag(self, newTag, rev=False):
        list = self.sender
        selectedRow = list.GetFirstSelected()
        while not -1 == selectedRow:
            rowKey = list.GetItemData(selectedRow)
            if not rev:
                if '+' == newTag[:1]:
                    self.model.addTag4Item(rowKey, newTag[1:])
                elif '-' == newTag[:1]:
                    self.model.rmvTag4Item(rowKey, newTag[1:])
            else:
                _tagSet = self.model.hasTag(rowKey, newTag)
                if _tagSet: self.model.rmvTag4Item(rowKey, newTag)
                else: self.model.addTag4Item(rowKey, newTag)
                
            selectedRow = list.GetNextSelected(selectedRow)
        
    def listBeginEdit(self, event):#disable edit: path, tags
        try:
            if READONLY == self.sender.columns[event.Column][3]:
                event.Veto()#Readonly
            else:
                self.oldval = event.Text
                ui_utils.log('edit item')
        except Exception, e:
            winlog(str(e), True)
        
    def pathListKeyDown(self, event):
        if wx.WXK_DELETE == event.GetKeyCode():
            self.pathDel()
        elif wx.WXK_F5 == event.GetKeyCode():
            self.pathSync()
    
    def itemListKeyDown(self, event):
        '''
        ^ [11] set/unset sys-new by click F11 
        ^ --------
        ^ [12] set/unset sys-del by click F12
        ^ --------
        '''
        if wx.WXK_DELETE == event.GetKeyCode():
            self.itemDel()
        elif wx.WXK_F2 == event.GetKeyCode():
            self.itemSetTag()
        elif wx.WXK_F8 == event.GetKeyCode():
            self.itemOpen()
        elif wx.WXK_F6 == event.GetKeyCode():
            for i in range(self.sender.GetItemCount()):
                self.sender.Select(i)
            
        elif wx.WXK_F11 == event.GetKeyCode():
            try:
                self._itemSetOneTag(SYS_TAG_NEW, True)
                self.model.refreshAll()
                self.model.saveItem()
                self.winlog('set tag done')
            except Exception, e:
                self.winlog(str(e), True)
                raise e
        elif wx.WXK_F12 == event.GetKeyCode():
            try:
                self._itemSetOneTag(SYS_TAG_DEL, True)
                self.model.refreshAll()
                self.model.saveItem()
                self.winlog('set tag done')
            except Exception, e:
                self.winlog(str(e), True)
                raise e
            
        elif wx.WXK_F5 == event.GetKeyCode():
            self.autoTag()
    
        
        
class FileDropTarget(wx.FileDropTarget):
    def __init__(self, window, model, winlog):
        wx.FileDropTarget.__init__(self)  
        window.SetDropTarget(self)
        self.dropFile = EventHandler(None, model, winlog).pathAdd
    def OnDropFiles(self, x, y, filenames):
        self.dropFile(x, y, filenames)            
#--------BEGIN UI
def makeMainWin():
    mainWin = MainWin()
    model = Model()
    mainWin.registerSearcher(EventHandler(None, model, mainWin.log).formularFilter)
    
    view1 = SplitView(mainWin.getViewPort())
    
    view2 = HtmlView(view1.p1, EventHandler(None, model, mainWin.log).tagFilter)
    model.refreshObj[TAG_CONFIG_F_NAME] = view2#view2.refreshData(model.tagHtmlStr)
    
    view3 = ListView(view1.p2, (('Pathes', 200, wx.LIST_FORMAT_LEFT, 'ro'), ))
    evtHandler = EventHandler(view3, model, mainWin.log)
    view3.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler.listBeginEdit)#must set for readonly
    #view3.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.listEndEdit)
    view3.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.pathListKeyDown)
    FileDropTarget(view3, model, mainWin.log)
    model.refreshObj[PATH_CONFIG_F_NAME] = view3#view3.refreshData(model.getPathes())
    
    view4 = ListView(view1.p3, model.itemcolumns)
    evtHandler = EventHandler(view4, model, mainWin.log, PATH_COL_IDX)#define key column
    view4.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, evtHandler.listBeginEdit)
    view4.Bind(wx.EVT_LIST_END_LABEL_EDIT, evtHandler.itemSet)
    view4.Bind(wx.EVT_LIST_KEY_DOWN, evtHandler.itemListKeyDown)
    #view4.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, evtHandler.itemOpen)#change to F8
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

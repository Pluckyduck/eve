#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/neocom/neocom/neocomSvc.py
import uicls
import uiconst
import blue
import util
import uiutil
import service
import base
import math
import uthread
import random
import form
import uix
import skillUtil
import neocom
import collections
import localization
import invCtrl
DEBUG_ALWAYSLOADRAW = False
NOTPERSISTED_BTNTYPES = (neocom.BTNTYPE_WINDOW,)
RAWDATA_NEOCOMDEFAULT = ((neocom.BTNTYPE_CHAT, 'chat', None),
 (neocom.BTNTYPE_CMD, 'inventory', None),
 (neocom.BTNTYPE_CMD, 'addressbook', None),
 (neocom.BTNTYPE_CMD, 'mail', None),
 (neocom.BTNTYPE_CMD, 'fitting', None),
 (neocom.BTNTYPE_CMD, 'market', None),
 (neocom.BTNTYPE_CMD, 'scienceandindustry', None),
 (neocom.BTNTYPE_CMD, 'corporation', None),
 (neocom.BTNTYPE_CMD, 'map', None),
 (neocom.BTNTYPE_CMD, 'assets', None),
 (neocom.BTNTYPE_CMD, 'wallet', None),
 (neocom.BTNTYPE_CMD, 'journal', None),
 (neocom.BTNTYPE_CMD, 'tutorial', None),
 (neocom.BTNTYPE_CMD, 'help', None))
RAWDATA_EVEMENU = ((neocom.BTNTYPE_GROUP, 'groupInventory', [(neocom.BTNTYPE_CMD, 'inventory', None),
   (neocom.BTNTYPE_CMD, 'activeShipCargo', None),
   (neocom.BTNTYPE_CMD, 'itemHangar', None),
   (neocom.BTNTYPE_CMD, 'shipHangar', None),
   (neocom.BTNTYPE_CMD, 'corpHangar', None),
   (neocom.BTNTYPE_CMD, 'corpDeliveriesHangar', None),
   (neocom.BTNTYPE_CMD, 'assets', None)]),
 (neocom.BTNTYPE_GROUP, 'groupAccessories', [(neocom.BTNTYPE_BOOKMARKS, 'bookmarkedsites', None),
   (neocom.BTNTYPE_CMD, 'browser', None),
   (neocom.BTNTYPE_CMD, 'calculator', None),
   (neocom.BTNTYPE_CMD, 'notepad', None),
   (neocom.BTNTYPE_CMD, 'log', None)]),
 (neocom.BTNTYPE_GROUP, 'groupBusiness', [(neocom.BTNTYPE_CMD, 'market', None),
   (neocom.BTNTYPE_CMD, 'contracts', None),
   (neocom.BTNTYPE_CMD, 'wallet', None),
   (neocom.BTNTYPE_CMD, 'scienceandindustry', None),
   (neocom.BTNTYPE_CMD, 'agentfinder', None),
   (neocom.BTNTYPE_CMD, 'militia', None),
   (neocom.BTNTYPE_CMD, 'bountyoffice', None)]),
 (neocom.BTNTYPE_GROUP, 'groupSocial', [(neocom.BTNTYPE_CMD, 'mail', None),
   (neocom.BTNTYPE_CMD, 'calendar', None),
   (neocom.BTNTYPE_CMD, 'corporation', None),
   (neocom.BTNTYPE_CMD, 'sovdashboard', None),
   (neocom.BTNTYPE_CMD, 'fleet', None),
   (neocom.BTNTYPE_CMD, 'chatchannels', None)]),
 (neocom.BTNTYPE_CMD, 'charactersheet', None),
 (neocom.BTNTYPE_CMD, 'certificates', None),
 (neocom.BTNTYPE_CMD, 'addressbook', None),
 (neocom.BTNTYPE_CMD, 'fitting', None),
 (neocom.BTNTYPE_CMD, 'map', None),
 (neocom.BTNTYPE_CMD, 'journal', None),
 (neocom.BTNTYPE_CMD, 'help', None),
 (neocom.BTNTYPE_CMD, 'tutorial', None))

class BtnDataRaw():

    def __init__(self, label = None, cmdName = None, guid = None, iconPath = None):
        self.label = label
        self.cmdName = cmdName
        self.guid = guid or cmdName
        self.iconPath = iconPath


BTNDATARAW_BY_ID = {'addressbook': BtnDataRaw(label='UI/Neocom/PeopleAndPlacesBtn', cmdName='OpenPeopleAndPlaces', guid='form.AddressBook', iconPath='ui_12_64_2'),
 'agentfinder': BtnDataRaw(label='UI/Neocom/AgentFinderBtn', cmdName='OpenAgentFinder', guid='form.AgentFinderWnd', iconPath='ui_57_64_17'),
 'assets': BtnDataRaw(label='UI/Neocom/AssetsBtn', cmdName='OpenAssets', guid='form.AssetsWindow', iconPath='ui_7_64_13'),
 'bookmarkedsites': BtnDataRaw(label='UI/Neocom/BrowserBookmarksBtn', iconPath='ui_36_64_15'),
 'bountyoffice': BtnDataRaw(label='UI/Station/BountyOffice/BountyOffice', cmdName='OpenBountyOffice', guid='form.BountyWindow', iconPath='61_2'),
 'browser': BtnDataRaw(label='UI/Neocom/BrowserBtn', cmdName='OpenBrowser', guid='uicls.BrowserWindow', iconPath='ui_9_64_4'),
 'calculator': BtnDataRaw(label='UI/Neocom/CalculatorBtn', cmdName='OpenCalculator', guid='form.Calculator', iconPath='ui_49_64_1'),
 'calendar': BtnDataRaw(label='UI/Neocom/CalendarBtn', cmdName='OpenCalendar', guid='form.eveCalendarWnd', iconPath='ui_94_64_12'),
 'certificates': BtnDataRaw(label='UI/Neocom/CertificatesBtn', cmdName='OpenCertificatePlanner', guid='form.certificateWindow', iconPath='ui_79_64_1'),
 'charactersheet': BtnDataRaw(label='UI/Neocom/CharacterSheetBtn', cmdName='OpenCharactersheet', guid='form.CharacterSheet', iconPath='ui_2_64_16'),
 'chat': BtnDataRaw(label='UI/Neocom/ChatBtn', cmdName='OpenChat', guid='form.LSCChannel', iconPath=neocom.ICONPATH_CHAT),
 'chatchannels': BtnDataRaw(label='UI/Neocom/ChatChannelsBtn', cmdName='OpenChannels', guid='form.Channels', iconPath='ui_9_64_2'),
 'contracts': BtnDataRaw(label='UI/Neocom/ContractsBtn', cmdName='OpenContracts', guid='form.ContractsWindow', iconPath='ui_64_64_10'),
 'corporation': BtnDataRaw(label='UI/Neocom/CorporationBtn', cmdName='OpenCorporationPanel', guid='form.Corporation', iconPath='ui_7_64_6'),
 'fitting': BtnDataRaw(label='UI/Neocom/FittingBtn', cmdName='OpenFitting', guid='form.FittingWindow', iconPath='ui_17_128_4'),
 'fleet': BtnDataRaw(label='UI/Neocom/FleetBtn', cmdName='OpenFleet', guid='form.FleetWindow', iconPath='ui_94_64_9'),
 'group': BtnDataRaw(label='UI/Neocom/ButtonGroup', iconPath=neocom.ICONPATH_GROUP),
 'groupInventory': BtnDataRaw(label='UI/Neocom/GroupInventory', iconPath=neocom.ICONPATH_GROUP),
 'groupAccessories': BtnDataRaw(label='UI/Neocom/GroupAccessories', iconPath=neocom.ICONPATH_GROUP),
 'groupBusiness': BtnDataRaw(label='UI/Neocom/GroupBusiness', iconPath=neocom.ICONPATH_GROUP),
 'groupSocial': BtnDataRaw(label='UI/Neocom/GroupSocial', iconPath=neocom.ICONPATH_GROUP),
 'help': BtnDataRaw(label='UI/Neocom/HelpBtn', cmdName='OpenHelp', guid='form.HelpWindow', iconPath='ui_74_64_14'),
 'inventory': BtnDataRaw(label='UI/Neocom/InventoryBtn', cmdName='OpenInventory', guid='form.InventoryPrimary', iconPath=form.Inventory.default_iconNum),
 'activeShipCargo': BtnDataRaw(label='UI/Neocom/ActiveShipCargoBtn', cmdName='OpenCargoHoldOfActiveShip', guid='form.ActiveShipCargo', iconPath='ui_1337_64_14'),
 'itemHangar': BtnDataRaw(label='UI/Neocom/ItemHangarBtn', cmdName='OpenHangarFloor', guid='form.StationItems', iconPath=invCtrl.StationItems.iconName),
 'shipHangar': BtnDataRaw(label='UI/Neocom/ShipHangarBtn', cmdName='OpenShipHangar', guid='form.StationShips', iconPath=invCtrl.StationShips.iconName),
 'corpHangar': BtnDataRaw(label='UI/Neocom/CorpHangarBtn', cmdName='OpenCorpHangar', guid='form.StationCorpHangars', iconPath='ui_1337_64_12'),
 'corpDeliveriesHangar': BtnDataRaw(label='UI/Neocom/DeliveriesHangarBtn', cmdName='OpenCorpDeliveries', guid='form.StationCorpDeliveries', iconPath='ui_1337_64_6'),
 'journal': BtnDataRaw(label='UI/Neocom/JournalBtn', cmdName='OpenJournal', guid='form.Journal', iconPath='ui_25_64_3'),
 'log': BtnDataRaw(label='UI/Neocom/logBtn', cmdName='OpenLog', guid='form.Logger', iconPath='ui_34_64_4'),
 'mail': BtnDataRaw(label='UI/Neocom/EvemailBtn', cmdName='OpenMail', guid='form.MailWindow', iconPath='ui_94_64_8'),
 'map': BtnDataRaw(label='UI/Neocom/MapBtn', cmdName='CmdToggleMap', iconPath='ui_7_64_4'),
 'market': BtnDataRaw(label='UI/Neocom/MarketBtn', cmdName='OpenMarket', guid='form.RegionalMarket', iconPath='ui_18_128_1'),
 'militia': BtnDataRaw(label='UI/FactionWarfare/FactionalWarfare', cmdName='OpenMilitia', guid='form.MilitiaWindow', iconPath='ui_61_128_3'),
 'navyoffices': BtnDataRaw(guid='form.MilitiaWindow'),
 'notepad': BtnDataRaw(label='UI/Neocom/NotepadBtn', cmdName='OpenNotepad', guid='form.Notepad', iconPath='ui_49_64_2'),
 'scienceandindustry': BtnDataRaw(label='UI/Neocom/ScienceAndIndustryBtn', cmdName='OpenScienceAndIndustry', guid='form.Manufacturing', iconPath='ui_57_64_9'),
 'sovdashboard': BtnDataRaw(label='UI/Neocom/SovereigntyBtn', cmdName='OpenSovDashboard', guid='form.SovereigntyOverviewWnd', iconPath='ui_57_64_18'),
 'tutorial': BtnDataRaw(label='UI/Shared/Tutorial', cmdName='OpenTutorial', guid='form.TutorialWindow', iconPath='ui_74_64_13'),
 'undock': BtnDataRaw(label='UI/Neocom/UndockBtn', cmdName='CmdExitStation'),
 'wallet': BtnDataRaw(label='UI/Neocom/WalletBtn', cmdName='OpenWallet', guid='form.Wallet', iconPath='ui_7_64_12')}

def ConvertOldTypeOfRawData(rawData):
    if isinstance(rawData, tuple):
        if len(rawData) == 3:
            btnType, id, children = rawData
        else:
            btnType, id, iconPath, children = rawData
        return util.KeyVal(btnType=btnType, id=id, children=children)
    return rawData


class NeocomSvc(service.Service):
    __update_on_reload__ = 1
    __guid__ = 'svc.neocom'
    __notifyevents__ = ['OnSessionChanged',
     'OnWindowOpened',
     'OnWindowClosed',
     'OnWindowMinimized',
     'OnWindowMaximized']

    def Run(self, *args):
        self.buttonDragOffset = None
        self.eveMenu = None
        self.folderDropCookie = None
        self.dragOverBtn = None
        self.currPanels = []
        self.neocom = None
        self.updatingWindowPush = False
        self.blinkQueue = []
        self.btnData = None
        self.blinkThread = None

    def Stop(self, memStream = None):
        self.CloseAllPanels()
        for cont in uicore.layer.sidePanels.children:
            if cont.name == 'Neocom':
                cont.Close()

        for cont in uicore.layer.abovemain.children:
            if isinstance(cont, neocom.PanelBase):
                cont.Close()

        if self.neocom:
            self.neocom.Close()
            self.neocom = None
        if self.blinkThread:
            self.blinkThread.kill()
            self.blinkThread = None

    def Reload(self):
        self.Stop()
        self.Run()
        if self.neocom:
            self.neocom.Close()
        self.CreateNeocom()
        self.UpdateNeocomButtons()

    def _CheckNewDefaultButtons(self, rawData):
        originalRawData = settings.char.ui.Get('neocomButtonRawDataOriginal', self._GetDefaultRawButtonData())
        newOriginalData = []
        for data in self._GetDefaultRawButtonData():
            data = ConvertOldTypeOfRawData(data)
            newOriginalData.append(data)
            if not self._IsWndIDInRawData(data.id, originalRawData):
                if not self._IsWndIDInRawData(data.id, rawData):
                    rawData.append(data)

        settings.char.ui.Set('neocomButtonRawDataOriginal', tuple(newOriginalData))

    def _GetDefaultRawButtonData(self):
        return RAWDATA_NEOCOMDEFAULT

    def _IsWndIDInRawData(self, checkWndID, rawData):
        if not rawData:
            return False
        for data in rawData:
            data = ConvertOldTypeOfRawData(data)
            if checkWndID == data.id or self._IsWndIDInRawData(checkWndID, data.children):
                return True

        return False

    def ResetEveMenuBtnData(self):
        self.eveMenuBtnData = BtnDataHeadNode('eveMenu', RAWDATA_EVEMENU, isRemovable=False, persistChildren=False)

    def OnSessionChanged(self, isRemote, sess, change):
        if 'stationid' in change:
            self.scopeSpecificBtnData = self.GetScopeSpecificButtonData(recreate=True)
            self.UpdateNeocomButtons()

    def CreateNeocom(self):
        if not self.btnData:
            rawData = settings.char.ui.Get('neocomButtonRawData', self._GetDefaultRawButtonData())
            self._CheckNewDefaultButtons(rawData)
            if DEBUG_ALWAYSLOADRAW:
                rawData = self._GetDefaultRawButtonData()
            self.btnData = BtnDataHeadNode('neocom', rawData)
            self.scopeSpecificBtnData = None
            self.ResetEveMenuBtnData()
        if not self.neocom:
            self.neocom = neocom.Neocom(parent=uicore.layer.sidePanels, idx=0)
            for wnd in uicore.registry.GetWindows():
                self.OnWindowOpened(wnd)

            for blinkData in self.blinkQueue:
                self.Blink(*blinkData)

            self.blinkQueue = []
        if self.blinkThread:
            self.blinkThread.kill()
            self.blinkThread = None
        self.blinkThread = uthread.new(self._BlinkThread)

    def _BlinkThread(self):
        while True:
            blue.synchro.SleepWallclock(neocom.BLINK_INTERVAL)
            sm.ScatterEvent('OnNeocomBlinkPulse')

    def OnWindowOpened(self, wnd):
        if not self.neocom:
            return
        if not wnd or wnd.destroyed:
            return
        if not wnd.IsKillable() or self._IsWindowIgnored(wnd):
            return
        for btnHeadData in (self.btnData, self.scopeSpecificBtnData):
            if not btnHeadData:
                continue
            for btnData in btnHeadData.children:
                if btnData.btnType != neocom.BTNTYPE_WINDOW and wnd.__guid__ == getattr(btnData, 'guid', None):
                    BtnDataNode(parent=btnData, children=None, iconPath=btnData.iconPath, label=wnd.GetCaption(), id=wnd.windowID, btnType=neocom.BTNTYPE_WINDOW, wnd=wnd, isDraggable=False)
                    btnData.SetActive()
                    return

        self.AddWindowButton(wnd)

    def ResetButtons(self):
        if uicore.Message('AskRestartNeocomButtons', {}, uiconst.YESNO) == uiconst.ID_YES:
            settings.char.ui.Set('neocomButtonRawData', None)
            settings.user.windows.Set('neocomWidth', neocom.Neocom.default_width)
            self.Reload()

    def _IsWindowIgnored(self, wnd):
        IGNORECLASSES = (uicls.WindowStack, form.LSCChannel, form.MapBrowserWnd)
        for classType in IGNORECLASSES:
            if isinstance(wnd, classType):
                return True

        if wnd.isModal:
            return True
        return False

    def AddWindowButton(self, wnd):
        btnData = self._GetBtnDataByGUID(wnd.__guid__)
        if not btnData:
            btnData = BtnDataNode(parent=self.btnData, children=None, iconPath=wnd.iconNum, label=wnd.GetCaption(), id=wnd.__guid__, guid=wnd.__guid__, btnType=neocom.BTNTYPE_WINDOW, isActive=True)
        BtnDataNode(parent=btnData, children=None, iconPath=wnd.iconNum, label=wnd.GetCaption(), id=wnd.windowID, btnType=neocom.BTNTYPE_WINDOW, wnd=wnd, isDraggable=False)
        if btnData and btnData.btnUI:
            btnData.btnUI.UpdateIcon()

    def _GetBtnDataByGUID(self, guid):
        if not guid:
            return
        for btnHeadData in (self.btnData, self.scopeSpecificBtnData):
            if not btnHeadData:
                continue
            for btnData in btnHeadData.children:
                if getattr(btnData, 'guid', None) == guid:
                    return btnData

    def RemoveWindowButton(self, wndID, wndCaption, wndGUID):
        btnData = self._GetBtnDataByGUID(wndGUID)
        if not btnData:
            return
        for btnChildData in btnData.children:
            wnd = getattr(btnChildData, 'wnd', None)
            if not wnd or wnd.destroyed or wnd.windowID == wndID:
                btnChildData.Remove()
            elif not wnd.IsKillable() and not wnd.IsMinimized():
                btnChildData.Remove()

        if not btnData.children:
            if btnData.btnType == neocom.BTNTYPE_WINDOW:
                btnData.Remove()
            else:
                btnData.SetInactive()

    def UpdateNeocomButtons(self):
        if self.neocom is not None:
            self.neocom.UpdateButtons()

    def OnWindowMinimized(self, wnd):
        if not self.neocom:
            return
        if not wnd or wnd.destroyed:
            return
        if not wnd.IsKillable():
            self.AddWindowButton(wnd)

    def OnWindowMaximized(self, wnd):
        if not self.neocom:
            return
        if not wnd or wnd.destroyed:
            return
        if not wnd.IsKillable():
            self.RemoveWindowButton(wnd.windowID, wnd.GetCaption(), wnd.__guid__)

    def OnWindowClosed(self, wndID, wndCaption, wndGUID):
        if not self.neocom:
            return
        self.RemoveWindowButton(wndID, wndCaption, wndGUID)

    def GetButtonData(self):
        return [ btnData for btnData in self.btnData.children if self.IsButtonInScope(btnData) ]

    def IsButtonInScope(self, btnData):
        if btnData.id in ('corpHangar', 'corpDeliveriesHangar') and util.IsNPCCorporation(session.corpid):
            return False
        if btnData.id == 'corpHangar' and sm.GetService('corp').GetOffice() is None:
            return False
        if btnData.guid and btnData.guid.startswith('form.'):
            _, windowName = btnData.guid.split('.')
            wndCls = getattr(form, windowName)
            scope = wndCls.default_scope
            if not scope:
                return True
            if session.stationid2 and scope != 'station':
                return False
            if session.solarsystemid and scope != 'space':
                return False
        return True

    def GetScopeSpecificButtonData(self, recreate = False):
        if session.stationid is not None:
            if recreate or self.scopeSpecificBtnData is None:
                self.scopeSpecificBtnData = self.GetStationButtonData()
        return self.scopeSpecificBtnData

    def GetStationButtonData(self):
        btnDataHead = BtnDataHeadNode('station', isRemovable=False, persistChildren=False)
        BtnDataNode(parent=btnDataHead, children=None, iconPath=neocom.ICONPATH_UNDOCK, label=localization.GetByLabel(BTNDATARAW_BY_ID['undock'].label), id='undock', guid=None, btnType=neocom.BTNTYPE_CMD, cmdName=BTNDATARAW_BY_ID['undock'].cmdName, isRemovable=False)
        return btnDataHead

    def OnButtonDragged(self, btn):
        self.CloseAllPanels()
        if not btn.parent:
            return
        l, t, w, h = btn.parent.GetAbsolute()
        relY = uicore.uilib.y - t
        if self.buttonDragOffset is None:
            self.buttonDragOffset = relY - btn.top
            btn.realTop = btn.top
        MIN = 0
        MAX = h - btn.height
        btn.top = max(MIN, min(relY - self.buttonDragOffset, MAX))
        self._CheckSwitch(btn)

    def OnButtonDragEnd(self, btnUI):
        folderBtnUI = self._GetButtonByXCoord(btnUI.top)
        if folderBtnUI and folderBtnUI != btnUI and isinstance(folderBtnUI, neocom.ButtonGroup):
            self.AddToFolder(btnUI, folderBtnUI)
        self.buttonDragOffset = None
        btnUI.top = btnUI.realTop

    def _CheckSwitch(self, dragBtn):
        switchBtn = self._GetButtonByXCoord(dragBtn.top)
        if self.dragOverBtn and switchBtn != self.dragOverBtn:
            self.dragOverBtn.OnDragExit()
        if switchBtn and switchBtn != dragBtn:
            if isinstance(switchBtn, neocom.ButtonGroup) and dragBtn.btnData.btnType not in neocom.FIXED_PARENT_BTNTYPES:
                self.dragOverBtn = switchBtn
                self.dragOverBtn.OnDragEnter(None, [dragBtn.btnData])
            else:
                switchTop = switchBtn.top
                switchBtn.top = dragBtn.realTop
                dragBtn.realTop = switchTop
                dragBtn.btnData.SwitchWith(switchBtn.btnData)
                switchBtn.OnSwitched()
        else:
            self.dragOverBtn = None

    def _GetButtonByXCoord(self, x, offset = True):
        buttons = self.GetButtonData()
        if not buttons:
            return None
        width = buttons[0].btnUI.width
        MIN = 0
        MAX = len(buttons)
        if offset:
            x += width / 2
        index = max(MIN, x / width)
        if index < MAX:
            button = buttons[index].btnUI
            if button.display:
                return button
        else:
            return None

    def IsDraggingButtons(self):
        return self.buttonDragOffset is not None

    def GetMinimizeToPos(self, wnd):
        if isinstance(wnd, uicls.WindowStack):
            wnd = wnd.GetActiveWindow()
        if isinstance(wnd, form.LSCChannel):
            btnData = self.btnData.GetBtnDataByTypeAndID(neocom.BTNTYPE_CHAT, 'chat')
        else:
            btnData = self._GetBtnDataByGUID(wnd.__guid__)
        if btnData and btnData.btnUI:
            if btnData.btnUI.state == uiconst.UI_HIDDEN:
                uiObj = self.neocom.overflowBtn
            else:
                uiObj = btnData.btnUI
            uiObj.BlinkOnce()
            l, t, w, h = uiObj.GetAbsolute()
            return (l + w / 2, t + h / 2)
        else:
            uiObj = self.neocom.buttonCont.children[-1]
            if uiObj.state == uiconst.UI_HIDDEN:
                uiObj = self.neocom.overflowBtn
                uiObj.BlinkOnce()
            l, t, w, h = uiObj.GetAbsolute()
            return (l + w / 2, t + h / 2)

    def Blink(self, wndID, hint = None, numBlinks = None):
        if not self.neocom:
            self.blinkQueue.append((wndID, hint, numBlinks))
            return
        if not self.IsBlinkingEnabled():
            return
        if wndID == 'charactersheet':
            self.neocom.charSheetBtn.EnableBlink()
            return
        if wndID == 'calendar':
            if form.eveCalendarWnd.GetIfOpen():
                return
            btnData = self.btnData.GetBtnDataByTypeAndID(neocom.BTNTYPE_CMD, wndID, recursive=True)
            if not btnData:
                self.neocom.clockCont.EnableBlink()
                return
        elif wndID == 'eveMenuBtn':
            self.eveMenuBtnData.isBlinking = True
            return
        headNodesToCheck = (self.btnData, self.scopeSpecificBtnData, self.eveMenuBtnData)
        for headBtnData in headNodesToCheck:
            if headBtnData is None:
                continue
            btnData = headBtnData.GetBtnDataByTypeAndID(neocom.BTNTYPE_CMD, wndID, recursive=True)
            if btnData:
                btnData.SetBlinkingOn(hint, numBlinks)
                return

    def BlinkOff(self, wndID):
        if wndID == 'calendar':
            self.neocom.clockCont.DisableBlink()
        if not self.neocom:
            return
        btnData = self.btnData.GetBtnDataByTypeAndID(neocom.BTNTYPE_CMD, wndID, recursive=True)
        if not btnData:
            return
        btnData.SetBlinkingOff()

    def AddToFolder(self, btnUI, folderBtnUI, *args):
        btnUI.btnData.MoveTo(folderBtnUI.btnData)

    def OnNeocomButtonsRecreated(self):
        self.dragOverBtn = None
        self.CloseAllPanels()

    def ShowPanel(self, triggerCont, panelClass, panelAlign, *args, **kw):
        panel = panelClass(idx=0, *args, **kw)
        self.currPanels.append(panel)
        uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEDOWN, self.OnGlobalMouseDown)
        self.CheckPanelPosition(panel, triggerCont, panelAlign)
        panel.EntryAnimation()
        return panel

    def CheckPanelPosition(self, panel, triggerCont, panelAlign):
        l, t, w, h = triggerCont.GetAbsolute()
        if panelAlign == neocom.PANEL_SHOWABOVE:
            panel.left = l
            panel.top = t - panel.height
            if panel.left + panel.width > uicore.desktop.width:
                panel.left = l - panel.width + w
        elif panelAlign == neocom.PANEL_SHOWONSIDE:
            if self.neocom.align == uiconst.TOLEFT:
                panel.left = l + w
            else:
                panel.left = l - panel.width
            panel.top = t
            if panel.top + panel.height > uicore.desktop.height - self.neocom.height:
                panel.top = t - panel.height + h
            if panel.left + panel.width > uicore.desktop.width:
                panel.left = l - panel.width
        dw = uicore.desktop.width
        dh = uicore.desktop.height
        if panel.top < 0:
            panel.top = 0
        elif panel.top + panel.height > dh:
            panel.top = dh - panel.height
        if panel.left < 0:
            panel.left = 0
        elif panel.left + panel.width > dw:
            panel.left = dw - panel.width

    def IsSomePanelOpen(self):
        return len(self.currPanels) > 0

    def OnGlobalMouseDown(self, cont, *args):
        if hasattr(cont, 'ToggleNeocomPanel'):
            return True
        if not isinstance(cont, neocom.PanelEntryBase):
            sm.ScatterEvent('OnNeocomPanelsClosed')
            self.CloseAllPanels()
            return False
        return True

    def CloseAllPanels(self):
        for panel in self.currPanels:
            panel.Close()

        self.currPanels = []

    def ClosePanel(self, panel):
        self.currPanels.remove(panel)
        panel.Close()

    def CloseChildrenPanels(self, btnData):
        toRemove = []
        for panel in self.currPanels:
            if panel.btnData and panel.btnData.IsDescendantOf(btnData):
                toRemove.append(panel)

        for panel in toRemove:
            panel.Close()
            self.currPanels.remove(panel)

    def ToggleEveMenu(self):
        if self.eveMenu and not self.eveMenu.destroyed:
            self.CloseAllPanels()
            self.eveMenu = None
        else:
            self.ShowEveMenu()

    def ShowEveMenu(self):
        self.neocom.UnhideNeocom(sleep=True)
        self.eveMenu = self.ShowPanel(self.neocom, neocom.PanelEveMenu, neocom.PANEL_SHOWONSIDE, parent=uicore.layer.abovemain, btnData=self.eveMenuBtnData)
        sm.ScatterEvent('OnEveMenuShown')
        return self.eveMenu

    def GetSideOffset(self):
        width = settings.user.windows.Get('neocomWidth', neocom.Neocom.default_width)
        align = settings.char.ui.Get('neocomAlign', neocom.Neocom.default_align)
        if align == uiconst.TOLEFT:
            return (width, 0)
        else:
            return (0, width)

    def GetUIObjectByID(self, wndID):
        if not self.neocom:
            return
        if wndID == 'charactersheet':
            return self.neocom.charSheetBtn
        if wndID == 'skillTrainingCont':
            return self.neocom.skillTrainingCont
        for btnData in (self.btnData, self.scopeSpecificBtnData):
            if btnData:
                node = btnData.GetBtnDataByTypeAndID(None, wndID, recursive=True)
                if node:
                    if node.btnUI.destroyed:
                        return
                    return node.btnUI

        node = self.eveMenuBtnData.GetBtnDataByTypeAndID(None, wndID, recursive=True)
        if node:
            return self.neocom.eveMenuBtn

    def IsButtonVisible(self, wndID):
        for btnData in (self.btnData, self.scopeSpecificBtnData):
            if btnData is None:
                continue
            node = btnData.GetBtnDataByTypeAndID(None, wndID)
            if node:
                return True

        return False

    def OnButtonDragEnter(self, btnData, dragBtnData, *args):
        if not self.IsValidDropData(dragBtnData):
            return
        btns = self.GetButtonData()
        if btnData in btns:
            index = btns.index(btnData)
        else:
            index = len(btns)
        self.neocom.ShowDropIndicatorLine(index)

    def OnButtonDragExit(self, *args):
        self.neocom.HideDropIndicatorLine()

    def OnBtnDataDropped(self, btnData, index = None):
        if not self.IsValidDropData(btnData):
            return
        oldHeadNode = btnData.GetHeadNode()
        oldBtnData = self.btnData.GetBtnDataByGUID(btnData.guid, recursive=False)
        if btnData.btnType == neocom.BTNTYPE_GROUP and oldHeadNode != self.btnData.GetHeadNode():
            toRemove = []
            for child in btnData.children:
                btnDataFound = self.btnData.GetBtnDataByGUID(child.guid, recursive=True)
                if btnDataFound:
                    toRemove.append(child)
                else:
                    child.isRemovable = True

            for child in toRemove:
                btnData.RemoveChild(child)

        btnData.MoveTo(self.btnData, index)
        if oldBtnData and oldBtnData != btnData:
            for child in oldBtnData.children:
                child.parent = btnData

            btnData.SetActive()
            oldBtnData.Remove()
        if oldHeadNode == self.eveMenuBtnData:
            self.ResetEveMenuBtnData()
            btnData.isRemovable = True

    def IsValidDropData(self, btnData):
        if not btnData:
            return False
        if isinstance(btnData, collections.Iterable):
            btnData = btnData[0]
        if not isinstance(btnData, BtnDataNode):
            return False
        if btnData.GetHeadNode() != self.btnData.GetHeadNode():
            if btnData.btnType == neocom.BTNTYPE_GROUP:
                if self.btnData.GetBtnDataByTypeAndID(neocom.BTNTYPE_GROUP, btnData.id, recursive=True):
                    return False
            else:
                foundBtnData = self.btnData.GetBtnDataByGUID(btnData.guid, recursive=True)
                if foundBtnData and foundBtnData.btnType != neocom.BTNTYPE_WINDOW:
                    return False
        return True

    def GetMenu(self):
        m = [(localization.GetByLabel('UI/Neocom/CreateNewGroup'), self.AddNewGroup), None]
        if self.neocom.IsSizeLocked():
            m.append((uiutil.MenuLabel('UI/Neocom/UnlockNeocom'), self.neocom.SetSizeLocked, (False,)))
        else:
            m.append((uiutil.MenuLabel('UI/Neocom/LockNeocom'), self.neocom.SetSizeLocked, (True,)))
        if self.neocom.IsAutoHideActive():
            m.append((uiutil.MenuLabel('UI/Neocom/AutohideOff'), self.neocom.SetAutoHideOff))
        else:
            m.append((uiutil.MenuLabel('UI/Neocom/AutohideOn'), self.neocom.SetAutoHideOn))
        if self.neocom.align == uiconst.TOLEFT:
            m.append((uiutil.MenuLabel('UI/Neocom/AlignRight'), self.neocom.SetAlignRight))
        else:
            m.append((uiutil.MenuLabel('UI/Neocom/AlignLeft'), self.neocom.SetAlignLeft))
        if self.IsBlinkingEnabled():
            m.append((uiutil.MenuLabel('UI/Neocom/ConfigBlinkOff'), self.SetBlinkingOff))
        else:
            m.append((uiutil.MenuLabel('UI/Neocom/ConfigBlinkOn'), self.SetBlinkingOn))
        m.append((uiutil.MenuLabel('UI/Neocom/ResetButtons'), self.ResetButtons))
        if eve.session.role & service.ROLEMASK_ELEVATEDPLAYER:
            m.extend([None, ('Reload Insider', sm.StartService('insider').Reload), ('Toggle Insider', lambda : sm.StartService('insider').Toggle(forceShow=True))])
        return m

    def AddNewGroup(self):
        wnd = form.NeocomGroupNamePopup.Open()
        ret = wnd.ShowModal()
        if ret in (uiconst.ID_CLOSE, uiconst.ID_CANCEL):
            return
        BtnDataNodeGroup(parent=self.btnData, children=[], iconPath=neocom.ICONPATH_GROUP, label=ret.label or localization.GetByLabel('UI/Neocom/ButtonGroup'), id='group_%s' % ret.label, btnType=neocom.BTNTYPE_GROUP, labelAbbrev=ret.labelAbbrev)

    def EditGroup(self, btnData):
        wnd = form.NeocomGroupNamePopup.Open(groupName=btnData.label, groupAbbrev=btnData.labelAbbrev)
        ret = wnd.ShowModal()
        if ret in (uiconst.ID_CLOSE, uiconst.ID_CANCEL):
            return
        btnData.label = ret.label or localization.GetByLabel('UI/Neocom/ButtonGroup')
        btnData.labelAbbrev = ret.labelAbbrev
        btnData.Persist()

    def SetBlinkingOn(self):
        settings.char.windows.Set('neoblink', True)

    def SetBlinkingOff(self):
        settings.char.windows.Set('neoblink', False)
        self.BlinkStopAll()

    def BlinkStopAll(self):
        self.eveMenuBtnData.SetBlinkingOff()
        self.btnData.SetBlinkingOff()
        self.neocom.charSheetBtn.DisableBlink()

    def IsBlinkingEnabled(self):
        return settings.char.windows.Get('neoblink', True)

    def GetMenuForBtnData(self, btnData):
        return []

    def GetButtonCmdHint(self, btnData):
        if btnData.id == 'wallet':
            return '<br><br>' + sm.GetService('wallet').GetWalletHint()
        if btnData.id == 'charactersheet':
            return '<br>' + cfg.eveowners.Get(session.charid).name
        return ''

    def ShowSkillNotification(self, skillTypeIDs):
        leftSide, rightSide = uicore.layer.sidePanels.GetSideOffset()
        sm.GetService('skills').ShowSkillNotification(skillTypeIDs, leftSide + 14)


class BtnDataNode(util.KeyVal):
    __guid__ = 'neocom.BtnDataNode'
    __notifyevents__ = []
    persistChildren = True

    def __init__(self, parent = None, children = None, iconPath = None, label = None, id = None, btnType = None, isRemovable = True, isDraggable = True, isActive = False, isBlinking = False, labelAbbrev = None, **kw):
        sm.RegisterNotify(self)
        self._parent = parent
        self.iconPath = iconPath
        self._children = children or []
        self.label = label
        self.labelAbbrev = labelAbbrev
        self.btnType = btnType
        self.btnUI = None
        self.isRemovable = isRemovable
        self.isDraggable = isDraggable
        self.isActive = isActive
        self.isBlinking = isBlinking
        self.blinkHint = ''
        self.blinkEndThread = None
        self.id = id
        self.guid = None
        for attrname, val in kw.iteritems():
            setattr(self, attrname, val)

        if parent:
            parent._AddChild(self)

    def _AddChild(self, child):
        self._children.append(child)
        self.CheckContinueBlinking()
        if self.persistChildren:
            self.Persist()

    def GetChildren(self):
        return self._children

    children = property(GetChildren)

    def GetParent(self):
        return self._parent

    def SetParent(self, parent):
        self.parent._children.remove(self)
        self.parent.CheckContinueBlinking()
        self._parent = parent
        self.Persist()

    parent = property(GetParent, SetParent)

    def __repr__(self):
        return '<BtnDataNode: %s - %s children>' % (repr(self.label), len(self._children))

    def Persist(self, scatterEvent = True, fromChild = False):
        if fromChild and not self.persistChildren:
            return
        self.parent.Persist(scatterEvent, fromChild=True)

    def GetRawData(self):
        return util.KeyVal(btnType=self.btnType, id=self.id, iconPath=self.iconPath, children=self._GetRawChildren())

    def _GetRawChildren(self):
        rawChildren = None
        if self._children:
            rawChildren = []
            if self.persistChildren:
                for btnData in self._children:
                    if btnData.btnType not in NOTPERSISTED_BTNTYPES:
                        rawChildren.append(btnData.GetRawData())

        return rawChildren

    def SwitchWith(self, other):
        if other.parent != self.parent:
            return
        lst = self.parent._children
        indexSelf = lst.index(self)
        indexOther = lst.index(other)
        lst[indexSelf] = other
        lst[indexOther] = self
        self.Persist(scatterEvent=False)

    def GetBtnDataByTypeAndID(self, btnType, id, recursive = False):
        for btnData in self._children:
            if btnType is None or btnData.btnType == btnType:
                if btnData.id == id:
                    return btnData
            if recursive:
                subBtnData = btnData.GetBtnDataByTypeAndID(btnType, id, True)
                if subBtnData:
                    return subBtnData

    def GetBtnDataByGUID(self, guid, recursive = False):
        if guid is None:
            return
        for btnData in self._children:
            if getattr(btnData, 'guid', None) == guid:
                return btnData
            if recursive:
                subBtnData = btnData.GetBtnDataByGUID(guid, True)
                if subBtnData:
                    return subBtnData

    def RemoveChild(self, btnData):
        btnData.parent = None
        self._children.remove(btnData)
        if self.persistChildren:
            self.Persist()

    def MoveTo(self, newParent, index = None):
        if newParent == self:
            return
        if not self.IsRemovable():
            return
        self.parent._children.remove(self)
        if index is None:
            newParent._children.append(self)
        else:
            newParent._children.insert(index, self)
        oldParent = self.parent
        self.parent = newParent
        oldParent.CheckContinueBlinking()
        self.Persist()
        oldParent.Persist()

    def Remove(self):
        self.parent.RemoveChild(self)

    def IsRemovable(self):
        if self.isRemovable:
            for btnData in self._children:
                if not btnData.IsRemovable():
                    return False

        return True

    def GetHeadNode(self):
        return self.parent.GetHeadNode()

    def IsDescendantOf(self, btnData):
        return self.parent._IsDescendantOf(btnData)

    def _IsDescendantOf(self, btnData):
        if self == btnData:
            return True
        return self.parent._IsDescendantOf(btnData)

    def SetBlinkingOn(self, hint = '', numBlinks = None):
        self.isBlinking = True
        self.blinkHint = hint
        if numBlinks:
            uthread.new(self._StopBlinkThread, numBlinks)
        if self.parent:
            self.parent.SetBlinkingOn(hint)
        sm.ScatterEvent('OnNeocomBlinkingChanged')

    def _StopBlinkThread(self, numBlinks):
        blue.synchro.SleepWallclock(numBlinks * neocom.BLINK_INTERVAL)
        self.SetBlinkingOff()

    def SetBlinkingOff(self):
        self._SetBlinkingOff()
        if self.parent:
            self.parent.CheckContinueBlinking()
        sm.ScatterEvent('OnNeocomBlinkingChanged')

    def _SetBlinkingOff(self):
        self.isBlinking = False
        self.blinkHint = ''
        for btnData in self._children:
            btnData._SetBlinkingOff()

    def CheckContinueBlinking(self):
        for btnData in self._children:
            if btnData.isBlinking:
                sm.ScatterEvent('OnNeocomBlinkingChanged')
                self.isBlinking = True
                return

        self.isBlinking = False
        if self.parent:
            self.parent.CheckContinueBlinking()
        else:
            sm.ScatterEvent('OnNeocomBlinkingChanged')

    def SetActive(self):
        self.isActive = True
        if hasattr(self.btnUI, 'CheckIfActive'):
            self.btnUI.CheckIfActive()

    def SetInactive(self):
        self.isActive = False
        if hasattr(self.btnUI, 'CheckIfActive'):
            self.btnUI.CheckIfActive()

    def GetHint(self, label = None):
        hintStr = label or self.label
        if self.btnType == neocom.BTNTYPE_CMD:
            cmd = uicore.cmd.commandMap.GetCommandByName(self.cmdName)
            shortcutStr = cmd.GetShortcutAsString()
            if shortcutStr:
                hintStr += ' [%s]' % shortcutStr
            if self.blinkHint:
                hintStr += '<br>%s' % self.blinkHint
            hintStr += sm.GetService('neocom').GetButtonCmdHint(self)
        return hintStr

    def GetMenu(self):
        m = []
        if self.isRemovable and not self.isActive:
            m.append((localization.GetByLabel('UI/Commands/Remove'), self.Remove))
        m += sm.GetService('neocom').GetMenuForBtnData(self)
        return m


class BtnDataHeadNode(BtnDataNode):
    __guid__ = 'neocom.BtnDataHeadNode'

    def __init__(self, id = None, rawBtnData = None, isRemovable = True, persistChildren = True):
        self.id = id
        self._parent = None
        self._persistThread = None
        rawBtnData = rawBtnData or []
        self._children = []
        self._GetButtonDataFromnRawData(self, rawBtnData, isRemovable)
        self.isBlinking = False
        self.persistChildren = persistChildren

    def __repr__(self):
        return '<BtnDataHeadNode: %s children>' % len(self._children)

    def Persist(self, scatterEvent = True, fromChild = False):
        if not self._persistThread:
            self._persistThread = uthread.new(self._Persist, scatterEvent)

    def _Persist(self, scatterEvent):
        if self.persistChildren:
            savedData = []
            for btnData in self._children:
                if btnData.btnType not in NOTPERSISTED_BTNTYPES:
                    savedData.append(btnData.GetRawData())

            settings.char.ui.Set('%sButtonRawData' % self.id, savedData)
        if scatterEvent:
            sm.ScatterEvent('OnHeadNodeChanged', self.id)
        self._persistThread = None

    def _GetButtonDataFromnRawData(self, parent, rawData, isRemovable):
        nodes = []
        for data in rawData:
            data = ConvertOldTypeOfRawData(data)
            nodeClass = NODECLASS_BY_TYPE.get(data.btnType, BtnDataNode)
            btnDataRaw = BTNDATARAW_BY_ID.get(data.id)
            if btnDataRaw:
                if data.Get('label', None):
                    label = data.label
                else:
                    label = localization.GetByLabel(btnDataRaw.label)
                iconPath = btnDataRaw.iconPath
                guid = btnDataRaw.guid
                cmdName = btnDataRaw.cmdName
            elif data.btnType == neocom.BTNTYPE_GROUP:
                label = data.label
                iconPath = neocom.ICONPATH_GROUP
                guid = data.id
                cmdName = None
            else:
                continue
            btnData = nodeClass(parent=parent, iconPath=iconPath, id=data.id, guid=guid, label=label, btnType=data.btnType, cmdName=cmdName, isRemovable=isRemovable, labelAbbrev=data.Get('labelAbbrev', None))
            if data.children:
                self._GetButtonDataFromnRawData(btnData, data.children, isRemovable)
            nodes.append(btnData)

        return nodes

    def GetHeadNode(self):
        return self

    def IsDescendantOf(self, btnData):
        return False

    def _IsDescendantOf(self, btnData):
        return btnData == self


class BtnDataNodeDynamic(BtnDataNode):
    __guid__ = 'neocom.BtnDataNodeDynamic'
    persistChildren = False

    def GetDataList(self):
        return []

    def GetNodeFromData(self, data, parent):
        pass

    def _AddChild(self, child):
        pass

    def OnNeocomBlinkPulse(self):
        pass

    def CheckContinueBlinking(self):
        pass

    def RemoveChild(self, btnData):
        pass

    def GetChildren(self):
        dataList = self.GetDataList()
        return self._GetChildren(dataList, self)

    def GetPanelEntryHeight(self):
        return 25

    def _GetChildren(self, dataList, parent = None):
        children = []
        entryHeight = self.GetPanelEntryHeight()
        maxEntries = uicore.desktop.height / entryHeight - 1
        for data in dataList[:maxEntries]:
            btnData = self.GetNodeFromData(data, parent)
            children.append(btnData)

        overflow = dataList[maxEntries:]
        if overflow:
            overflowBtnData = BtnDataNode(parent=parent, iconPath=neocom.ICONPATH_GROUP, label=localization.GetByLabel('UI/Neocom/OverflowButtonsLabel', numButtons=len(overflow)), btnType=neocom.BTNTYPE_GROUP, panelEntryHeight=entryHeight, isRemovable=False, isDraggable=False)
            children.append(overflowBtnData)
            self._GetChildren(dataList[maxEntries:], overflowBtnData)
        return children

    children = property(GetChildren)


class BtnDataNodeGroup(BtnDataNode):
    __guid__ = 'neocom.BtnDataNodeGroup'

    def GetMenu(self):
        if self.GetHeadNode() == sm.GetService('neocom').eveMenuBtnData:
            return
        m = []
        if self.IsRemovable():
            m.append((uiutil.MenuLabel('UI/Commands/Remove'), self.Remove, ()))
            m.append((localization.GetByLabel('UI/Neocom/Edit'), sm.GetService('neocom').EditGroup, (self,)))
        return m

    def GetRawData(self):
        return util.KeyVal(btnType=self.btnType, id=self.id, iconPath=self.iconPath, children=self._GetRawChildren(), label=self.label, labelAbbrev=self.labelAbbrev)


class BtnDataNodeBookmarks(BtnDataNodeDynamic):
    __guid__ = 'neocom.BtnDataNodeBookmarks'

    def GetDataList(self):
        bookmarkBtnData = []
        bookmarkData = sm.GetService('sites').GetBookmarks()[:]
        bookmarkData.insert(0, util.KeyVal(url='home', name=localization.GetByLabel('UI/Neocom/Homepage')))
        return bookmarkData

    def GetNodeFromData(self, bookmark, parent):
        return neocom.BtnDataNode(parent=parent, children=None, iconPath=neocom.ICONPATH_BOOKMARKS, label=bookmark.name, id=bookmark.name, btnType=neocom.BTNTYPE_BOOKMARK, bookmark=bookmark, isRemovable=False, isDraggable=False)


class BtnDataNodeChat(BtnDataNodeDynamic):
    __guid__ = 'neocom.BtnDataNodeChat'
    __notifyevents__ = ['OnNeocomBlinkPulse']

    def GetMenu(self):
        return [(localization.GetByLabel('UI/Commands/OpenChannels'), uicore.cmd.OpenChannels, [])]

    def OnNeocomBlinkPulse(self):
        self.isBlinking = False
        if sm.GetService('neocom').IsBlinkingEnabled():
            for wnd in self._GetOpenChatWindows():
                if getattr(wnd, 'isBlinking', False):
                    if wnd.InStack() and wnd.GetStack().display:
                        continue
                    self.isBlinking = True
                    return

    def _GetOpenChatWindows(self):
        return [ wnd for wnd in uicore.registry.GetWindows() if wnd.__class__ == form.LSCChannel ]

    def GetDataList(self):

        def GetKey(wnd):
            priority = ('chatchannel_solarsystemid2', 'chatchannel_corpid', 'chatchannel_allianceid', 'chatchannel_fleetid', 'chatchannel_squadid', 'chatchannel_wingid')
            if wnd.name in priority:
                return priority.index(wnd.name)
            else:
                return wnd.GetCaption()

        sortedData = sorted(self._GetOpenChatWindows(), key=GetKey)
        data = uiutil.Bunch(addChatChannelWnd=1)
        sortedData.insert(0, data)
        return sortedData

    def GetNodeFromData(self, wnd, parent):
        if getattr(wnd, 'addChatChannelWnd', False):
            return BtnDataNode(parent=parent, children=None, iconPath=neocom.ICONPATH_CHAT, label=localization.GetByLabel(BTNDATARAW_BY_ID['chatchannels'].label), id='chatchannels', guid=None, btnType=neocom.BTNTYPE_CMD, cmdName=BTNDATARAW_BY_ID['chatchannels'].cmdName, isRemovable=False, isDraggable=False)
        else:
            return BtnDataNode(parent=parent, iconPath=neocom.ICONPATH_CHAT, label=wnd.GetCaption(), id=wnd.windowID, btnType=neocom.BTNTYPE_CHATCHANNEL, wnd=wnd, isRemovable=False, isDraggable=False, isBlinking=getattr(wnd, 'isBlinking', False))


NODECLASS_BY_TYPE = {neocom.BTNTYPE_CHAT: BtnDataNodeChat,
 neocom.BTNTYPE_BOOKMARKS: BtnDataNodeBookmarks,
 neocom.BTNTYPE_GROUP: BtnDataNodeGroup}

class NeocomGroupNamePopup(uicls.Window):
    __guid__ = 'form.NeocomGroupNamePopup'
    default_windowID = 'NeocomGroupNamePopup'
    default_topParentHeight = 0
    default_fixedWidth = 180
    default_fixedHeight = 130
    default_caption = 'UI/Neocom/NeocomGroup'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.btnData = attributes.get('btnData', None)
        groupName = attributes.get('groupName', '')
        groupAbbrev = attributes.get('groupAbbrev', '')
        self.sr.main.padLeft = 6
        self.sr.main.padRight = 6
        self.sr.main.padBottom = 4
        self.labelEdit = uicls.SinglelineEdit(name='labelEdit', label=localization.GetByLabel('UI/Neocom/NeocomGroupName'), parent=self.sr.main, align=uiconst.TOTOP, padTop=20, setvalue=groupName, OnReturn=self.Confirm)
        self.labelEdit.SetMaxLength(30)
        self.labelAbbrevEdit = uicls.SinglelineEdit(name='labelAbbrevEdit', label=localization.GetByLabel('UI/Neocom/NeocomGroupNameAbbrev'), parent=self.sr.main, align=uiconst.TOTOP, padTop=20, setvalue=groupAbbrev, OnReturn=self.Confirm)
        self.labelAbbrevEdit.SetMaxLength(2)
        btns = uicls.ButtonGroup(parent=self.sr.main, line=False, btns=((localization.GetByLabel('UI/Common/Confirm'), self.Confirm, ()), (localization.GetByLabel('UI/Commands/Cancel'), self.Close, ())))

    def Confirm(self, *args):
        kv = util.KeyVal(label=self.labelEdit.GetValue(), labelAbbrev=self.labelAbbrevEdit.GetValue())
        self.SetModalResult(kv)
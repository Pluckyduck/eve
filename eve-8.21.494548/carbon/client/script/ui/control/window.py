#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/control/window.py
import blue
import telemetry
import uthread
import types
import log
import sys
import base
import mathUtil
import uicls
import uiutil
import uiconst
import trinity
import localization
POSOVERLAPSHIFT = 11

class WindowCore(uicls.Area):
    __guid__ = 'uicls.WindowCore'
    isDragObject = True
    isTopLevelWindow = True
    default_width = 256
    default_height = 128
    default_minSize = (default_width, default_height)
    default_maxSize = (None, None)
    default_fixedHeight = None
    default_fixedWidth = None
    default_left = '__center__'
    default_top = '__center__'
    default_name = 'window'
    default_idx = 0
    default_windowID = None
    default_stackID = None
    default_args = ()
    default_caption = None
    default_align = uiconst.RELATIVE
    default_showBottomLine = True
    default_openMinimized = False
    default_isKillable = True
    default_isMinimizable = True
    default_isStackable = True
    default_isCompactable = False
    SNAP_DISTANCE = 16

    @classmethod
    def Reload(cls, instance):
        attributes = instance.attributesBunch
        state = instance.state
        if instance.isDialog:
            instance.Close()
            return
        attributes.openMinimized = instance.IsMinimized()
        instance.Close()
        wnd = cls.Open(**attributes)
        wnd.SetState(state)

    def __init__(self, **kw):
        uicls.Area.__init__(self, **kw)
        notifyevents = getattr(self, '__notifyevents__', None)
        if not notifyevents:
            notifyevents = ['OnUIRefresh']
        elif 'OnUIRefresh' not in notifyevents:
            notifyevents.append('OnUIRefresh')
        self.__notifyevents__ = notifyevents
        sm.RegisterNotify(self)

    @apply
    def displayRect():
        doc = '\n            displayRect is a tuple of (displayX,displayY,displayWidth,displayHeight).\n            Prefer this over setting x, y, width and height separately if all are\n            being set.\n            '

        def fget(self):
            return (self._displayX,
             self._displayY,
             self._displayWidth,
             self._displayHeight)

        def fset(self, value):
            displayX, displayY, displayWidth, displayHeight = value
            self._displayX = int(round(displayX))
            self._displayY = int(round(displayY))
            self._displayWidth = int(round(displayWidth))
            self._displayHeight = int(round(displayHeight))
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight

        return property(**locals())

    def OnUIRefresh(self):
        self.Reload(self)

    def AutoFit(self):
        for each in uicore.desktop.children[:]:
            if each.name == 'debug':
                each.Close()

        data = []

        def CrawlAutoFit(obj, data, lvl = 0):
            if not obj.display:
                return
            if obj.align != uiconst.TOALL:
                data.append((obj.align, obj.GetAbsolute()))
            if hasattr(obj, 'children'):
                for each in obj.children:
                    CrawlAutoFit(each, data, lvl + 1)

        for each in self.children:
            CrawlAutoFit(each, data)

        for align, pos in data:
            if align in (uiconst.TOPLEFT,):
                uicls.Fill(parent=uicore.desktop, name='debug', idx=0, align=uiconst.TOPLEFT, pos=pos)

    def ApplyAttributes(self, attributes):
        self.startingup = True
        self.ResetAttributes()
        self._CheckCallableDefaults()
        self.attributesBunch = attributes
        self.windowID = attributes.get('windowID', self.default_windowID)
        uicore.registry.RegisterWindow(self)
        left, top, width, height = self.GetDefaultSizeAndPosition()
        attributes['left'] = left
        attributes['top'] = top
        if self.windowID:
            try:
                attributes.name = str(self.windowID)
            except Exception as e:
                attributes.name = repr(self.windowID)

        self.stackID = attributes.get('stackID', self.default_stackID)
        self.minsize = attributes.get('minSize', self.minsize)
        self.maxsize = attributes.get('maxSize', self.maxsize)
        self.showBottomLine = attributes.get('showBottomLine', self.default_showBottomLine)
        uicls.Area.ApplyAttributes(self, attributes)
        self.cacheContents = True
        self.InitializeSize(useDefaultPos=attributes.get('useDefaultPos', False))
        self.Prepare_()
        sm.ScatterEvent('OnWindowOpened', self)

    def PostApplyAttributes(self, attributes):
        self.RegisterPositionAndSize('width')
        self.RegisterPositionAndSize('height')
        if attributes.get('openDragging', False) and uicore.uilib.leftbtn:
            self.RegisterStackID(None)
            self._SetOpen(True)
            uthread.new(self._OpenDraggingThread)
        else:
            self.InitializeStatesAndPosition(showIfInStack=attributes.get('showIfInStack', True), useDefaultPos=attributes.get('useDefaultPos', False))
        caption = attributes.get('caption', self.default_caption)
        if caption is not None:
            self.SetCaption(caption)
        if attributes.get('openMinimized', self.default_openMinimized):
            self.Minimize(animate=False)
        self.startingup = False

    def _OpenDraggingThread(self):
        self.state = uiconst.UI_NORMAL
        self.left = uicore.uilib.x
        self.top = uicore.uilib.y - 5
        uicore.uilib.SetMouseCapture(self)
        compact = self.GetRegisteredState('compact')
        if compact:
            self.Compact()
        self._BeginDrag()

    def GetAbsolutePosition(self):
        return (self.left, self.top)

    def _CheckCallableDefaults(self):
        if callable(self.default_left):
            self.default_left = self.default_left()
        if callable(self.default_top):
            self.default_top = self.default_top()
        if callable(self.default_width):
            self.default_width = self.default_width()
        if callable(self.default_height):
            self.default_height = self.default_height()

    def Prepare_(self):
        self.Prepare_Header_()
        self.Prepare_LoadingIndicator_()
        self.Prepare_Background_()
        self.Prepare_ScaleAreas_()

    def Prepare_HeaderButtons_(self):
        if self.sr.headerButtons:
            self.sr.headerButtons.Close()
        self.sr.headerButtons = uicls.Container(name='headerButtons', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPRIGHT, parent=self, pos=(5, 0, 0, 16), idx=0)
        if self.InStack():
            closehint = localization.GetByLabel('/Carbon/UI/Controls/Window/CloseWindowStack')
            minimizehint = localization.GetByLabel('/Carbon/UI/Controls/Window/MinimizeWindowStack')
        else:
            closehint = localization.GetByLabel('/Carbon/UI/Common/Close')
            minimizehint = localization.GetByLabel('/Carbon/UI/Controls/Window/Minimize')
        w = 0
        for icon, name, hint, showflag, clickfunc, menufunc in [(102,
          'close',
          closehint,
          self.IsKillable(),
          self.CloseByUser,
          False), (103,
          'minimize',
          minimizehint,
          self.IsMinimizable(),
          self.Minimize,
          False)]:
            if not showflag:
                continue
            btn = uicls.ImageButton(name=name, parent=self.sr.headerButtons, align=uiconst.TOPRIGHT, state=uiconst.UI_NORMAL, pos=(w,
             0,
             16,
             16), idleIcon='ui_1_16_%s' % icon, mouseoverIcon='ui_1_16_%s' % (icon + 16), mousedownIcon='ui_1_16_%s' % (icon + 32), onclick=clickfunc, getmenu=menufunc, expandonleft=True, hint=hint)
            w += 15

        self.sr.headerButtons.width = w
        if self.sr.captionParent:
            self.sr.captionParent.padRight = w + 6

    def Prepare_Header_(self):
        if self.sr.headerParent:
            self.sr.headerParent.Close()
        self.sr.headerParent = uicls.Container(parent=self.sr.maincontainer, name='__headerParent', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP, pos=(0, 0, 0, 18), idx=0)
        self.sr.captionParent = uicls.Container(parent=self.sr.headerParent, name='__captionParent', state=uiconst.UI_PICKCHILDREN, clipChildren=True)
        self.sr.caption = uicls.Label(parent=self.sr.captionParent, name='__caption', state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, idx=0, pos=(8, 0, 0, 0), uppercase=uiconst.WINHEADERUPPERCASE, fontsize=uiconst.WINHEADERFONTSIZE, letterspace=uiconst.WINHEADERLETTERSPACE)

    def Update_Header_(self):
        self.SetCaption(self._caption or 'Window')

    def Prepare_Background_(self):
        self.LoadUnderlay(color=(0.5, 0.5, 0.5, 1.0), offset=-8, iconPath='ui_2_32_8', cornerSize=14)

    def Prepare_ScaleAreas_(self):
        if not self.sr.resizers:
            self.sr.resizers = uicls.Container(name='resizers', parent=self, state=uiconst.UI_PICKCHILDREN, idx=0)
        self.sr.resizers.Flush()
        if not self.IsResizeable() or self.InStack():
            return
        for name, align, w, h, cursor in [('sLeftTop',
          uiconst.TOPLEFT,
          8,
          8,
          15),
         ('sRightTop',
          uiconst.TOPRIGHT,
          6,
          6,
          13),
         ('sRightBottom',
          uiconst.BOTTOMRIGHT,
          8,
          8,
          15),
         ('sLeftBottom',
          uiconst.BOTTOMLEFT,
          8,
          8,
          13),
         ('sLeft',
          uiconst.TOLEFT,
          4,
          0,
          16),
         ('sRight',
          uiconst.TORIGHT,
          4,
          0,
          16),
         ('sTop',
          uiconst.TOTOP,
          0,
          4,
          17),
         ('sBottom',
          uiconst.TOBOTTOM,
          0,
          4,
          17)]:
            r = uicls.Fill(name=name, parent=self.sr.resizers, state=uiconst.UI_NORMAL, align=align, pos=(0,
             0,
             w,
             h), color=(0.0, 0.0, 0.0, 0.0))
            r.OnMouseDown = (self.StartScale, r)
            r.OnMouseUp = (self.EndScale, r)
            r.cursor = cursor

        for each in self.sr.resizers.children:
            if self._fixedHeight and each.name in ('sTop', 'sBottom', 'sRightTop', 'sLeftTop', 'sRightBottom', 'sLeftBottom'):
                each.state = uiconst.UI_HIDDEN
            if self._fixedWidth and each.name in ('sLeft', 'sRight', 'sRightTop', 'sLeftTop', 'sRightBottom', 'sLeftBottom'):
                each.state = uiconst.UI_HIDDEN

    def Prepare_LoadingIndicator_(self):
        if self.sr.loadingParent:
            self.sr.loadingParent.Close()
        self.sr.loadingParent = uicls.Container(name='__loadingParent', parent=self.sr.maincontainer, state=uiconst.UI_HIDDEN, idx=0)
        self.sr.loadingIndicator = uicls.AnimSprite(parent=self.sr.loadingParent, state=uiconst.UI_HIDDEN, align=uiconst.TOPRIGHT, left=5)

    def ResetAttributes(self):
        self._grab = [0, 0]
        self._dragging = False
        self._draginited = False
        self._scaling = False
        self._ret = None
        self._changing = False
        self._requesthideload = False
        self._caption = ''
        self._fixedWidth = self.default_fixedWidth
        self._fixedHeight = self.default_fixedHeight
        self._splitList = []
        self._collapsed = False
        self._locked = False
        self._minimized = 0
        self._open = False
        self._compact = False
        self.isModal = False
        self.isDialog = False
        self.snapGrid = None
        self._killable = self.default_isKillable
        self._minimizable = self.default_isMinimizable
        self._stackable = self.default_isStackable
        self._compactable = self.default_isCompactable
        self._resizeable = True
        self._collapseable = 1
        self.headerIconNo = None
        self.headerIconHint = None
        self.sr.minimizedBtn = None
        self.sr.tab = None
        self.sr.caption = None
        self.sr.modalParent = None
        self.sr.buttonParent = None
        self.sr.loadingParent = None
        self.sr.headerIcon = None
        self.sr.headerLine = None
        self.sr.headerButtonsTimer = None
        self.sr.resizers = None
        self.sr.stack = None
        self.sr.headerParent = None
        self.sr.headerButtons = None
        self.sr.captionParent = None
        self.sr.loadingIndicator = None
        width = self.default_width
        height = self.default_height
        self.minsize = self.default_minSize
        self.maxsize = self.default_maxSize

    def GetMainArea(self):
        return self.sr.maincontainer

    def InStack(self):
        return bool(self.sr.stack)

    def GetStack(self):
        return self.sr.stack

    def GetStackID(self):
        if self.windowID:
            all = settings.char.windows.Get('stacksWindows', {})
            if type(self.windowID) == tuple:
                windowID, subWindowID = self.windowID
            else:
                windowID = self.windowID
            if windowID in all:
                return all[windowID]
            return all.get(windowID, self.stackID)

    def RegisterStackID(self, stack = None):
        if self.windowID:
            all = settings.char.windows.Get('stacksWindows', {})
            if type(self.windowID) == tuple:
                windowID, subWindowID = self.windowID
            else:
                windowID = self.windowID
            if stack:
                all[windowID] = stack.windowID
            else:
                all[windowID] = None
            settings.char.windows.Set('stacksWindows', all)

    def InitializeSize(self, useDefaultPos = False):
        d = uicore.desktop
        if useDefaultPos:
            left, top, width, height = self.GetDefaultSizeAndPosition()
        else:
            left, top, width, height, dw, dh = self.GetRegisteredPositionAndSize()
        maxWidth, maxHeight = self.GetMaxWidth(), self.GetMaxHeight()
        minWidth, minHeight = self.GetMinWidth(), self.GetMinHeight()
        if self._fixedWidth:
            self.width = self._fixedWidth
        else:
            self.width = min(maxWidth, max(minWidth, min(d.width, width)))
        if self._fixedHeight:
            self.height = self._fixedHeight
        else:
            self.height = min(maxHeight, max(minHeight, min(d.height, height)))

    def GetStackClass(self):
        return uicls.WindowStackCore

    def InitializeStatesAndPosition(self, showIfInStack = True, useDefaultPos = False, **kwds):
        self.startingup = 1
        log.LogInfo('Window.InitializeStatesAndPosition', self.windowID)
        if self.IsMinimized():
            if self.sr.minimizedBtn:
                self.sr.minimizedBtn.Close()
                self.sr.minimizedBtn = None
                self.ArrangeMinimizedButtons()
            self._SetMinimized(False)
        compact = self.GetRegisteredState('compact')
        if compact:
            self.Compact()
        stack = None
        stackID = self.GetStackID()
        if not isinstance(self, uicls.WindowStackCore):
            if self.IsStackable() and stackID:
                stack = uicore.registry.GetWindow(stackID)
                if stack:
                    log.LogInfo('Window.InitializeStatesAndPosition, windowStack already created', self.windowID)
                    stack.InsertWnd(self, False, showIfInStack, 1)
        if not stack:
            collapsed = self.GetRegisteredState('collapsed')
            if collapsed:
                self.Collapse()
            elif self.IsCollapsed():
                self.Expand()
            self.UpdatePosition(useDefaultPos)
            if stackID is not None and not isinstance(self, self.GetStackClass()):
                self.state = uiconst.UI_HIDDEN
                log.LogInfo('Window.InitializeStatesAndPosition creating new stack while initializing', self.windowID)
                stack = uicore.registry.GetStack(stackID, self.GetStackClass())
                if stack:
                    stack.InsertWnd(self, True, showIfInStack, 1)
        focus = uicore.registry.GetFocus()
        if not (focus and (isinstance(focus, uicls.EditCore) or isinstance(focus, uicls.SinglelineEditCore))):
            uthread.new(uicore.registry.SetFocus, self)
        if not self.InStack() and not self.IsMinimized():
            self.state = uiconst.UI_NORMAL
        self._SetOpen(True)
        self.startingup = 0

    def UpdatePosition(self, useDefaultPos = False):
        if useDefaultPos:
            left, top, width, height = self.GetDefaultSizeAndPosition()
        else:
            left, top, width, height, dw, dh = self.GetRegisteredPositionAndSize()
        left = max(0, min(uicore.desktop.width - self.width, left))
        top = max(0, min(uicore.desktop.height - self.height, top))
        leftpush, rightpush = self.GetSideOffset()
        if left in (0, self.SNAP_DISTANCE):
            left += leftpush
        elif left + self.width in (uicore.desktop.width, uicore.desktop.width - self.SNAP_DISTANCE):
            left -= rightpush
        self.left = left
        self.top = top
        self.CheckWndPos()

    @classmethod
    def GetSideOffset(cls):
        return (0, 0)

    def RegisterState(self, statename):
        if self.windowID is None:
            return
        val = getattr(self, statename, 'notset')
        if val == 'notset':
            return
        if type(self.windowID) == tuple:
            windowID, subWindowID = self.windowID
        else:
            windowID = self.windowID
        all = settings.char.windows.Get('%sWindows' % statename[1:], {})
        all[windowID] = val
        settings.char.windows.Set('%sWindows' % statename[1:], all)

    def GetRegisteredState(self, statename):
        if self.windowID is None:
            return 0
        if type(self.windowID) == tuple:
            windowID, subWindowID = self.windowID
        else:
            windowID = self.windowID
        all = settings.char.windows.Get('%sWindows' % statename, {})
        if windowID in all:
            return all[windowID]
        if hasattr(self, 'default_%s' % statename):
            return getattr(self, 'default_%s' % statename)

    def RegisterPositionAndSize(self, key = None, windowID = None):
        if self.windowID is None:
            return
        if self._changing or self.IsMinimized():
            return
        if windowID is None:
            if type(self.windowID) == tuple:
                windowID, subWindowID = self.windowID
            else:
                windowID = self.windowID
        if self.InStack():
            l, t = self.sr.stack.left, self.sr.stack.top
            w, h = self.sr.stack.width, self.sr.stack.height
            cl, ct, cw, ch, cdw, cdh = self.sr.stack.GetRegisteredPositionAndSize()
        else:
            if self.GetStackID():
                return
            if self.GetAlign() != uiconst.RELATIVE:
                return
            l, t = self.left, self.top
            w, h = self.width, self.height
        if key is not None:
            cl, ct, cw, ch, cdw, cdh = self.GetRegisteredPositionAndSize()
            if key == 'left':
                t, w, h = ct, cw, ch
            elif key == 'top':
                l, w, h = cl, cw, ch
            elif key == 'width':
                l, t, h = cl, ct, ch
            elif key == 'height':
                l, t, w = cl, ct, cw
        if self.IsCollapsed():
            cl, ct, cw, ch, cdw, cdh = self.GetRegisteredPositionAndSize()
            h = ch
        dw, dh = uicore.desktop.width, uicore.desktop.height
        leftOffset, rightOffset = self.GetSideOffset()
        if l in (leftOffset, leftOffset + 16):
            l -= leftOffset
        elif l + w in (dw - rightOffset, dw - rightOffset - 16):
            l += rightOffset
        all = settings.char.windows.Get('windowSizesAndPositions_1', {})
        all[windowID] = (l,
         t,
         w,
         h,
         dw,
         dh)
        settings.char.windows.Set('windowSizesAndPositions_1', all)
        if isinstance(self, self.GetStackClass()):
            for each in self.GetWindows():
                each.RegisterPositionAndSize()

    def SetFixedHeight(self, height = None):
        self._fixedHeight = height

    def SetFixedWidth(self, width = None):
        self._fixedWidth = width

    def GetMinSize(self, *args, **kw):
        w, h = uicls.Area.GetMinSize(self, *args, **kw)
        if self.sr.buttonParent:
            bw, bh = self._GetMinSize(self.sr.buttonParent)
            w = max(w, bw)
            h = max(h, bh)
        if self.sr.headerParent and self.sr.headerParent.state != uiconst.UI_HIDDEN:
            h += self.sr.headerParent.height
        return (w, h)

    def IsCurrentDialog(self):
        ret = getattr(self, 'isDialog', False) and (not getattr(self, 'isModal', False) or uicore.registry.GetModalWindow() == self)
        return ret

    def Close(self, setClosed = False, *args, **kwds):
        if setClosed:
            self._SetOpen(False)
        sm.ScatterEvent('OnWindowClosed', self.windowID, self.GetCaption(), self.__guid__)
        if self._ret:
            self.SetModalResult(uiconst.ID_CLOSE, 'Close')
            return
        self.state = uiconst.UI_HIDDEN
        uicore.registry.CheckMoveActiveState(self)
        minimizedBtn = self.sr.minimizedBtn
        modalParent = self.sr.modalParent
        stack = self.GetStack()
        uicls.Area.Close(self)
        if self._ret:
            self.SetModalResult(uiconst.ID_CLOSE, '_OnClose')
            return
        if minimizedBtn:
            minimizedBtn.Close()
            self.ArrangeMinimizedButtons()
        if modalParent is not None and not modalParent.destroyed:
            modalParent.Close()
        uicore.registry.UnregisterWindow(self)
        if stack is not None and not stack.destroyed:
            stack.Check(checknone=1)

    def HasPendingModalResult(self):
        return bool(self._ret)

    def CloseByUser(self, *args):
        self.Close(setClosed=True)

    def ShowHeaderButtons(self, refresh = False, *args):
        if refresh and self.sr.headerButtons:
            self.sr.headerButtons.Close()
            self.sr.headerButtons = None
        if self.InStack() or self.GetAlign() != uiconst.TOPLEFT or uicore.uilib.leftbtn:
            return
        if self.sr.headerParent and self.sr.headerParent.state == uiconst.UI_HIDDEN:
            return
        if not self.sr.headerButtons:
            self.Prepare_HeaderButtons_()
        if self.sr.headerButtons:
            w = self.sr.headerButtons.width
            if self.sr.captionParent:
                self.sr.captionParent.padRight = w + 6
            if self.sr.loadingIndicator:
                self.sr.loadingIndicator.left = w
            self.sr.headerButtons.Show()
            self.sr.headerButtonsTimer = base.AutoTimer(1000, self.CloseHeaderButtons)

    def CloseHeaderButtons(self, destroy = False, *args):
        if uicore.uilib.mouseOver is self or uiutil.IsUnder(uicore.uilib.mouseOver, self):
            return
        if self.sr.headerButtons:
            if destroy:
                self.sr.headerButtons.Close()
                self.sr.headerButtons = None
            else:
                self.sr.headerButtons.Hide()
        self.sr.headerButtonsTimer = None
        if self.sr.captionParent:
            self.sr.captionParent.padRight = 6
        if self.sr.loadingIndicator:
            self.sr.loadingIndicator.left = 5

    def _OnResize(self, *args, **kw):
        uicls.Area._OnResize(self, *args, **kw)
        if not getattr(self, 'startingup', True):
            self.RegisterPositionAndSize()
        if self.OnResize_:
            self.OnResize_(self)

    def HideHeader(self):
        self._collapseable = 0
        if self.sr.headerParent:
            self.sr.headerParent.state = uiconst.UI_HIDDEN

    def ShowHeader(self):
        self._collapseable = 1
        if self.sr.headerParent:
            self.sr.headerParent.state = uiconst.UI_PICKCHILDREN

    def ShowBackground(self):
        self.Prepare_Background_()

    def HideBackground(self):
        self.LoadUnderlay(color=(0.5, 0.5, 0.5, 0.0))

    def Blink(self):
        stack = self.sr.stack
        if self.state == uiconst.UI_HIDDEN and self.sr.tab and hasattr(self.sr.tab, 'Blink'):
            self.sr.tab.Blink(1)
        if self.state == uiconst.UI_HIDDEN and self.sr.minimizedBtn and hasattr(self.sr.minimizedBtn, 'SetBlink'):
            self.sr.minimizedBtn.SetBlink(1)
        elif stack is not None and (stack.state != uiconst.UI_NORMAL or self.state != uiconst.UI_NORMAL):
            if stack.sr.minimizedBtn and hasattr(stack.sr.minimizedBtn, 'SetBlink'):
                stack.sr.minimizedBtn.SetBlink(1)

    def GetMenu(self, *args):
        menu = []
        if self.IsKillable():
            menu.append((uiutil.MenuLabel('/Carbon/UI/Common/Close'), self.CloseByUser))
        if not self.InStack() and self.IsMinimizable():
            if not getattr(self, 'isModal', 0):
                if self.state == uiconst.UI_NORMAL:
                    menu.append((uiutil.MenuLabel('/Carbon/UI/Controls/Window/Minimize'), self.ToggleVis))
                else:
                    menu.append((uiutil.MenuLabel('/Carbon/UI/Controls/Window/Maximize'), self.ToggleVis))
        return menu

    def ShowLoad(self, doBlock = True):
        self._requesthideload = False
        if self.sr.loadingParent:
            if doBlock:
                self.sr.loadingParent.state = uiconst.UI_NORMAL
            else:
                self.sr.loadingParent.state = uiconst.UI_DISABLED
            if self.sr.loadingIndicator and hasattr(self.sr.loadingIndicator, 'Play'):
                if not (self.InStack() or self.GetAlign() != uiconst.RELATIVE):
                    self.sr.loadingIndicator.sr.hint = localization.GetByLabel('/Carbon/UI/Controls/Window/Loading')
                    self.sr.loadingIndicator.Play()
        if not self.destroyed and self._requesthideload:
            self.HideLoad()

    def HideLoad(self):
        if self.sr.loadingIndicator and hasattr(self.sr.loadingIndicator, 'Stop'):
            self.sr.loadingIndicator.Stop()
        if self.sr.loadingParent:
            self.sr.loadingParent.state = uiconst.UI_HIDDEN
        self._requesthideload = True

    def ShowModal(self):
        return self.ShowDialog(modal=True)

    def ShowDialog(self, modal = False, state = uiconst.UI_NORMAL):
        self.isDialog = True
        self.isModal = modal
        self.state = uiconst.UI_HIDDEN
        self.MakeUnMinimizable()
        if modal:
            if self.parent and not self.parent.destroyed and self.parent.name[:8] == 'l_modal_':
                self.parent.SetOrder(0)
            else:
                myLayer = uicls.Container(name='l_modal_%s' % self.name, state=uiconst.UI_NORMAL, parent=uicore.layer.modal, idx=0)
                uiutil.Transplant(self, myLayer)
                self.sr.modalParent = myLayer
                self.ModalPosition()
            uicore.registry.AddModalWindow(self)
        self._ret = uthread.Channel()
        self.state = state
        if modal:
            uicore.registry.SetFocus(self)
        self.HideLoad()
        ret = self._ret.receive()
        return ret

    def ModalPosition(self):
        otherModal = uicore.registry.GetModalWindow()
        if otherModal and otherModal.state == uiconst.UI_NORMAL and otherModal.parent.state == uiconst.UI_NORMAL:
            self.left = otherModal.left + 16
            self.top = otherModal.top + 16
            if self.left + self.width > uicore.desktop.width:
                self.left = 0
            if self.top + self.height > uicore.desktop.height:
                self.top = 0
        else:
            cameraOffset = self.__class__.GetDefaultLeftOffset(self.width, align=uiconst.CENTER, left=0)
            self.left = (uicore.desktop.width - self.width) / 2 + cameraOffset
            self.top = (uicore.desktop.height - self.height) / 2

    def ButtonResult(self, button, *args):
        if self.IsCurrentDialog():
            self.SetModalResult(button.btn_modalresult, 'ButtonResult')

    def __ConfirmFunction(self, button, *args):
        uicore.registry.Confirm(button)

    def SetButtons(self, buttons, okLabel = None, okFunc = None, cancelLabel = None, cancelFunc = None, defaultBtn = None, okModalResult = None):
        if okLabel is None:
            okLabel = localization.GetByLabel('UI/Common/Buttons/OK')
        if cancelLabel is None:
            cancelLabel = localization.GetByLabel('UI/Common/Buttons/Cancel')
        if self.sr.buttonParent is None:
            self.sr.buttonParent = self.Split(uiconst.SPLITBOTTOM, 24, line=0)
        self.sr.buttonParent.Flush()
        if buttons is None:
            self.sr.buttonParent.state = uiconst.UI_HIDDEN
            return
        okFunc = okFunc or self.__ConfirmFunction
        cancelFunc = cancelFunc or self.ButtonResult
        btns = []
        if buttons in (uiconst.YESNO, uiconst.YESNOCANCEL):
            yesLabel = localization.GetByLabel('UI/Common/Buttons/Yes')
            noLabel = localization.GetByLabel('UI/Common/Buttons/No')
            btns.append(self.GetButtonData('YES', defaultBtn, yesLabel))
            btns.append(self.GetButtonData('NO', defaultBtn, noLabel))
        if buttons in (uiconst.OKCANCEL, uiconst.YESNOCANCEL):
            btns.append(self.GetButtonData('CANCEL', defaultBtn, cancelLabel, cancelFunc))
        if buttons in (uiconst.OKCLOSE, uiconst.CLOSE):
            closeLabel = localization.GetByLabel('UI/Common/Buttons/Close')
            btns.append(self.GetButtonData('CLOSE', defaultBtn, closeLabel, self.CloseByUser))
        if buttons in (uiconst.OK, uiconst.OKCANCEL, uiconst.OKCLOSE) or not btns:
            btns.insert(0, self.GetButtonData('OK', defaultBtn, okLabel, okFunc, okModalResult))
        bg = uicls.ButtonGroup(parent=self.sr.buttonParent.sr.content, btns=btns, buttonClass=getattr(self, '_buttonClass', uicls.Button), line=self.showBottomLine)
        self.sr.buttonParent.height = bg.height + 8
        self.sr.buttonParent.state = uiconst.UI_PICKCHILDREN

    def SetButtonClass(self, buttonClass):
        self._buttonClass = buttonClass

    def GetButtonData(self, btnStringID, defaultBtnID, label = None, func = None, btnID = None):
        if btnID is None:
            btnID = getattr(uiconst, 'ID_%s' % btnStringID, -1)
        bd = uiutil.Bunch()
        bd.label = label or btnStringID
        bd.func = func or self.ButtonResult
        bd.args = None
        bd.btn_modalresult = btnID
        bd.btn_default = bool(btnID == defaultBtnID)
        bd.btn_cancel = bool(btnStringID in ('CANCEL', 'CLOSE'))
        bdList = [bd.label,
         bd.func,
         bd.args,
         0,
         bd.btn_modalresult,
         bd.btn_default,
         bd.btn_cancel]
        return bdList

    def SetModalResult(self, result, caller = None):
        if self._ret:
            uicore.registry.RemoveModalWindow(self)
            self._ret.send(result)
            self._ret = None
            self.Close()

    def MakeUnResizeable(self):
        self._resizeable = False
        self.Prepare_ScaleAreas_()
        self.MakeUnstackable()
        self.RefreshHeaderButtonsIfVisible()

    def IsMinimizable(self):
        return self._minimizable

    def MakeUnMinimizable(self):
        self._minimizable = False
        self.RefreshHeaderButtonsIfVisible()

    def MakeUnKillable(self):
        self._killable = False
        self.RefreshHeaderButtonsIfVisible()

    def MakeKillable(self):
        self._killable = True
        self.RefreshHeaderButtonsIfVisible()

    def IsCompactable(self):
        return self._compactable

    def IsCompact(self):
        return self._compact

    def _SetCompact(self, isCompact):
        self._compact = isCompact
        self.RegisterState('_compact')
        self.RefreshHeaderButtonsIfVisible()

    def IsKillable(self):
        return self._killable

    def MakeUnstackable(self):
        self._stackable = False
        self.RefreshHeaderButtonsIfVisible()

    def MakeStackable(self):
        self._stackable = True
        self.RefreshHeaderButtonsIfVisible()

    def MakeCollapseable(self):
        self._collapseable = True
        self.RefreshHeaderButtonsIfVisible()

    def MakeUncollapseable(self):
        self._collapseable = False
        self.RefreshHeaderButtonsIfVisible()

    def IsResizeable(self):
        return self._resizeable and not self.IsLocked()

    def Lock(self, initing = False):
        self._locked = True
        self.RefreshHeaderButtonsIfVisible()

    def Unlock(self, initing = False):
        self._locked = False
        self.RefreshHeaderButtonsIfVisible()

    def IsLocked(self):
        return self._locked

    def RefreshHeaderButtonsIfVisible(self):
        if self.sr.headerButtons is None:
            return
        if self.sr.headerButtons.state != uiconst.UI_HIDDEN:
            self.ShowHeaderButtons(refresh=True)
        else:
            self.sr.headerButtons.Close()
            self.sr.headerButtons = None

    def SetMinSize(self, size, refresh = 0):
        self.minsize = size
        if self.GetAlign() == uiconst.RELATIVE and not self.InStack():
            if not self.IsCollapsed():
                if self.height < self.minsize[1]:
                    self.height = self.minsize[1]
                if self.width < self.minsize[0]:
                    self.width = self.minsize[0]
                if refresh:
                    self.width, self.height = self.minsize
        if self.InStack():
            self.sr.stack.SetMinWH()

    def SetMaxSize(self, size, refresh = 0):
        self.maxsize = size
        maxWidth, maxHeight = size
        if self.GetAlign() == uiconst.RELATIVE:
            if not self.IsCollapsed():
                if maxWidth is not None and self.width > maxWidth:
                    self.width = maxWidth
                if maxHeight is not None and self.height > maxHeight:
                    self.height = maxHeight
                if refresh:
                    if maxWidth is not None:
                        self.width = maxWidth
                    if maxHeight is not None:
                        self.height = maxHeight
        if self.InStack():
            self.sr.stack.Check()

    def SetCaption(self, caption, *args, **kwds):
        if localization.IsValidLabel(caption):
            self._caption = localization.GetByLabel(caption)
        else:
            self._caption = caption
        if self.sr.caption is None:
            return
        self.sr.caption.text = self._caption
        if self.sr.headerParent:
            self.sr.headerParent.height = max(16, self.sr.caption.textheight + 4)
        if self.sr.minimizedBtn and hasattr(self.sr.minimizedBtn, 'SetLabel'):
            self.sr.minimizedBtn.SetLabel(self._caption)
        if self.sr.tab and hasattr(self.sr.tab, 'SetLabel'):
            self.sr.tab.SetLabel(self._caption)

    def GetCaption(self, update = 1):
        self.UpdateCaption_(self)
        return self._caption

    def LockHeight(self, height):
        self._fixedHeight = height
        if not self.InStack():
            self.height = height

    def UnlockHeight(self):
        self._fixedHeight = None

    def LockWidth(self, width):
        self._fixedWidth = width
        if self.sr.stack is None:
            self.width = width

    def UnlockWidth(self):
        self._fixedWidth = None

    def ToggleVis(self, *args):
        if self.state != uiconst.UI_HIDDEN:
            uicore.registry.CheckMoveActiveState(self)
            self.Minimize()
        else:
            self.Maximize()

    def Maximize(self, *args, **kwds):
        if self.destroyed:
            return
        self._changing = True
        if self.sr.minimizedBtn:
            self.sr.minimizedBtn.Close()
            self.sr.minimizedBtn = None
            self.ArrangeMinimizedButtons()
        if self.InStack():
            self._SetMinimized(False)
            self.sr.stack.ShowWnd(self)
            self.sr.stack.Maximize()
            self._changing = False
            return
        self.OnStartMaximize_(self)
        if self.IsCollapsed():
            self.Expand(0)
        self.SetOrder(0)
        self._SetMinimized(False)
        self.state = uiconst.UI_NORMAL
        self.InitializeSize()
        self.InitializeStatesAndPosition()
        kick = [ w for w in self.Find('trinity.Tr2Sprite2dContainer') + self.Find('trinity.Tr2Sprite2d') if hasattr(w, '_OnResize') ]
        for each in kick:
            if hasattr(each, '_OnResize'):
                each._OnResize()

        uicore.registry.SetFocus(self)
        self.OnEndMaximize_(self)
        self._changing = False
        sm.ScatterEvent('OnWindowMaximized', self)

    Show = Maximize

    def Hide(self, *args, **kw):
        uicls.Area.Hide(self, *args, **kw)
        uicore.registry.CheckMoveActiveState(self)

    def Minimize(self, animate = True):
        if self.InStack():
            return self.sr.stack.Minimize(animate=animate)
        self._Minimize(animate=animate)

    def IsMinimized(self):
        if self.InStack():
            return bool(self.sr.stack.IsMinimized())
        return bool(self._minimized)

    def _SetMinimized(self, isMinimized):
        self._minimized = isMinimized
        self.RegisterState('_minimized')

    def IsCollapsed(self):
        if self.InStack():
            return bool(self.sr.stack.IsCollapsed())
        return bool(self._collapsed)

    def _SetCollapsed(self, isCollapsed):
        self._collapsed = isCollapsed
        self.RegisterState('_collapsed')

    def _SetOpen(self, isOpen):
        self._open = isOpen
        self.RegisterState('_open')

    def _Minimize(self, animate = True):
        if self.destroyed or self.IsMinimized() or self.sr.minimizedBtn:
            return
        self.OnStartMinimize_(self)
        self._changing = True
        uicore.registry.CheckMoveActiveState(self)
        btn = uicls.WindowMinimizeButton(parent=uicore.layer.abovemain, wnd=self, name='windowButton_%s' % repr(self.windowID), align=uiconst.BOTTOMLEFT, state=uiconst.UI_NORMAL, pos=(0, 0, 100, 18), idx=0)
        self.sr.minimizedBtn = btn
        self.ArrangeMinimizedButtons()
        if animate and not self.IsHidden():
            myPos = self.GetAbsolute()
            uthread.new(self._DisplayMinimizing, btn, myPos)
        if self.destroyed:
            return
        self._SetMinimized(True)
        self.state = uiconst.UI_HIDDEN
        self.OnEndMinimize_(self)
        self._changing = False
        sm.ScatterEvent('OnWindowMinimized', self)

    def _DisplayMinimizing(self, button, myPos):
        l, t, w, h = self.GetAbsolute()
        frame = uicls.Frame(parent=self.parent, align=uiconst.TOPLEFT, pos=myPos)
        fl, ft, fw, fh = myPos
        tl, tt, tw, th = button.GetAbsolute()
        fromVec = trinity.TriVector(float(fl), float(ft), 0.0)
        toVec = trinity.TriVector(float(tl), float(tt), 0.0)
        dist = (fromVec - toVec).Length()
        try:
            start = blue.os.GetWallclockTime()
            time = max(50, min(100.0, dist * 0.33))
            ndt = 0.0
            while ndt != 1.0:
                ndt = min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / time, 1.0)
                frame.top = int(mathUtil.Lerp(ft, tt, ndt))
                frame.left = int(mathUtil.Lerp(fl, tl, ndt))
                frame.width = int(mathUtil.Lerp(fw, tw, ndt))
                portion = frame.width / float(fw)
                frame.height = int(fh * portion)
                blue.pyos.synchro.Yield()

        finally:
            if frame is not None and not frame.destroyed:
                frame.Close()

    def ArrangeMinimizedButtons(self):
        if not self.parent:
            return
        l = 140
        for each in uicore.layer.abovemain.children:
            if isinstance(each, uicls.WindowMinimizeButton):
                each.left = l
                l += each.width

    def OnMouseEnter(self, *args):
        self.Prepare_ScaleAreas_()
        self.ShowHeaderButtons()

    def OnMouseExit(self, *args):
        self.CloseHeaderButtons()

    def OnMouseDown(self, btnNum, *args):
        if btnNum != uiconst.MOUSELEFT:
            return
        self.OnMouseDown_(self)
        self.CloseHeaderButtons()
        if self.IsLocked():
            self.DisableDrag()
        else:
            self.EnableDrag()
        self.SetOrder(0)

    def GetDragClipRects(self, shiftGroup, ctrlGroup):
        ml, mt, mw, mh = self.GetAbsolute()
        sl, st, sw, sh = self.GetGroupAbsolute(shiftGroup)
        cl, ct, cw, ch = self.GetGroupAbsolute(ctrlGroup)
        pl, pt, pw, ph = self.parent.GetAbsolute()
        x, y = uicore.uilib.x, uicore.uilib.y
        return ((0,
          y - mt,
          pw,
          ph - (mt + self.GetCollapsedHeight() - y) + 1), (x - sl,
          y - st,
          pw - (sl + sw - x) + 1,
          ph - (st + sh - y) + 1), (x - cl,
          y - ct,
          pw - (cl + cw - x) + 1,
          ph - (ct + ch - y) + 1))

    def _BeginDrag(self):
        self._dragging = True
        ctrlDragWindows = self.FindConnectingWindows('bottom')
        shiftDragWindows = self.FindConnectingWindows()
        self.PrepareWindowsForMove(shiftDragWindows)
        while not self.destroyed and self.IsBeingDragged():
            if uicore.uilib.mouseTravel > 1:
                break
            blue.pyos.synchro.Yield()

        if self.destroyed or not self.IsBeingDragged() or self._draginited:
            return
        if ctrlDragWindows is None:
            ctrlDragWindows = self.FindConnectingWindows('bottom')
        if shiftDragWindows is None:
            shiftDragWindows = self.FindConnectingWindows()
            self.PrepareWindowsForMove(shiftDragWindows)
        snapGrid = None
        snapGroup = None
        snapIndicator = self.GetSnapIndicator()
        allGrid, myGrid, shiftGrid, ctrlGrid = self.CreateSnapGrid(shiftDragWindows, ctrlDragWindows)
        myRect, shiftRect, ctrlRect = self.GetDragClipRects(shiftDragWindows, ctrlDragWindows)
        self._draginited = 1
        while not self.destroyed and self.IsBeingDragged() and uicore.uilib.leftbtn and self.GetAlign() == uiconst.RELATIVE:
            self.state = uiconst.UI_DISABLED
            shift = uicore.uilib.Key(uiconst.VK_SHIFT)
            ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
            self.left = uicore.uilib.x - self._grab[0]
            self.top = uicore.uilib.y - self._grab[1]
            for each in shiftDragWindows:
                if each == self:
                    continue
                if shift or ctrl and each in ctrlDragWindows:
                    each.left = uicore.uilib.x - each._grab[0]
                    each.top = uicore.uilib.y - each._grab[1]
                else:
                    each.left = each.preDragAbs[0]
                    each.top = each.preDragAbs[1]

            self.SetOrder(0)
            self.FindWindowToStackTo()
            if shift:
                snapGrid = shiftGrid
                snapGroup = shiftDragWindows
                cursorRect = shiftRect
            elif ctrl:
                cursorRect = ctrlRect
                snapGrid = ctrlGrid
                snapGroup = ctrlDragWindows
            else:
                snapGrid = myGrid
                snapGroup = [self]
                cursorRect = myRect
            uicore.uilib.ClipCursor(*cursorRect)
            self.ShowSnapEdges_Moving(snapGroup, snapGrid, snapIndicator=snapIndicator)
            self.OnDragTick()
            blue.pyos.synchro.Yield()

        if not self.InStack() and self.IsStackable():
            trystackto = self.FindWindowToStackTo()
            self.ClearStackIndication()
            if trystackto:
                if trystackto.sr.stack:
                    trystackto.sr.stack.CheckStack(self)
                else:
                    trystackto.CheckStack(self)
        uicore.uilib.UnclipCursor()
        if self.destroyed:
            return
        if not self.InStack() and snapGrid and snapGroup:
            self.ShowSnapEdges_Moving(snapGroup, snapGrid, doSnap=True)
        self.CleanupParent('snapIndicator')
        self.ClearStackIndication()
        if self.InStack():
            self.state = uiconst.UI_PICKCHILDREN
        else:
            self.state = uiconst.UI_NORMAL
        if not self.destroyed:
            self._draginited = 0

    def GetOtherWindows(self, useMe = False, checkAlign = False):
        validWnds = []
        if self.parent:
            for wnd in self.parent.children:
                if checkAlign and wnd.GetAlign() != uiconst.RELATIVE:
                    continue
                if wnd == self and useMe:
                    validWnds.append(wnd)
                    continue
                if not isinstance(wnd, uicls.WindowCore) or wnd == self or wnd.state == uiconst.UI_HIDDEN:
                    continue
                validWnds.append(wnd)

        return validWnds

    def CreateSnapGrid(self, shiftGroup = None, ctrlGroup = None):
        leftOffset, rightOffset = self.GetSideOffset()
        allWnds = self.GetOtherWindows()
        desk = uicore.desktop
        hAxes = [0,
         desk.height,
         16,
         desk.height - 16]
        vAxes = [0,
         leftOffset,
         leftOffset + 16,
         desk.width - rightOffset,
         desk.width - 16 - rightOffset]
        if leftOffset < settings.char.windows.Get('snapdistance', 12):
            vAxes.pop(0)
        hAxesWithOutMe = hAxes[:]
        vAxesWithOutMe = vAxes[:]
        hAxesWithOutShiftGroup = hAxes[:]
        vAxesWithOutShiftGroup = vAxes[:]
        hAxesWithOutCtrlGroup = hAxes[:]
        vAxesWithOutCtrlGroup = vAxes[:]
        hLists = [hAxes,
         hAxesWithOutMe,
         hAxesWithOutShiftGroup,
         hAxesWithOutCtrlGroup]
        vLists = [vAxes,
         vAxesWithOutMe,
         vAxesWithOutShiftGroup,
         vAxesWithOutCtrlGroup]
        for wnd in allWnds:
            l, t, w, h = wnd.GetAbsolute()
            self.AddtoAxeList(wnd, vLists, l, shiftGroup, ctrlGroup)
            self.AddtoAxeList(wnd, vLists, l + w, shiftGroup, ctrlGroup)
            self.AddtoAxeList(wnd, hLists, t, shiftGroup, ctrlGroup)
            self.AddtoAxeList(wnd, hLists, t + h, shiftGroup, ctrlGroup)

        self.snapGrid = [(hAxes, vAxes),
         (hAxesWithOutMe, vAxesWithOutMe),
         (hAxesWithOutShiftGroup, vAxesWithOutShiftGroup),
         (hAxesWithOutCtrlGroup, vAxesWithOutCtrlGroup)]
        return self.snapGrid

    def AddtoAxeList(self, wnd, lists, val, shiftgroup, ctrlgroup):
        all, minusMe, minusShiftGroup, minusCtrlGroup = lists
        if val not in all:
            all.append(val)
        if wnd != self and val not in minusMe:
            minusMe.append(val)
        if shiftgroup and wnd not in shiftgroup and val not in minusShiftGroup:
            minusShiftGroup.append(val)
        if ctrlgroup and wnd not in ctrlgroup and val not in minusCtrlGroup:
            minusCtrlGroup.append(val)

    def ShowSnapEdges_Scaling(self, snapGrid, showSnap = True, doSnap = False):
        horizontal, vertical = snapGrid
        snapdist = settings.char.windows.Get('snapdistance', 12)
        if not snapdist:
            self.HideSnapIndicator()
            return
        match = {}
        for side in self.scaleSides:
            wnd = self
            minLDist = 1000
            minRDist = 1000
            minTDist = 1000
            minBDist = 1000
            wl, wt, ww, wh = wnd.GetAbsolute()
            if showSnap:
                snapIndicator = wnd.GetSnapIndicator()
                snapIndicator.left = wl
                snapIndicator.top = wt
                snapIndicator.width = ww
                snapIndicator.height = wh
                for each in snapIndicator.children:
                    each.state = uiconst.UI_HIDDEN

            else:
                wnd.HideSnapIndicator()
            if side in ('top', 'bottom'):
                for hAxe in horizontal:
                    tDist = abs(hAxe - wt)
                    bDist = abs(hAxe - (wt + wh))
                    if side == 'top' and tDist <= snapdist and tDist < minTDist:
                        minTDist = tDist
                        match[side, wnd] = hAxe
                    elif side == 'bottom' and bDist <= snapdist and bDist < minBDist:
                        minBDist = bDist
                        match[side, wnd] = hAxe

            elif side in ('left', 'right'):
                for vAxe in vertical:
                    lDist = abs(vAxe - wl)
                    rDist = abs(vAxe - (wl + ww))
                    if side == 'left' and lDist <= snapdist and lDist < minLDist:
                        minLDist = lDist
                        match[side, wnd] = vAxe
                    elif side == 'right' and rDist <= snapdist and rDist < minRDist:
                        minRDist = rDist
                        match[side, wnd] = vAxe

        if showSnap or doSnap:
            checkMultipleSideSnap = {}
            for side, wnd in match.iterkeys():
                if wnd not in checkMultipleSideSnap:
                    checkMultipleSideSnap[wnd] = []
                snapValue = match[side, wnd]
                wl, wt, ww, wh = wnd.GetAbsolute()
                minH = wnd.GetMinHeight()
                snapIndicator = wnd.GetSnapIndicator()
                snapIndicator.state = uiconst.UI_DISABLED
                snapIndicator.SetOrder(1)
                if side == 'left':
                    if doSnap:
                        wnd.left = snapValue
                        if wnd.IsResizeable():
                            wnd.width = wl - snapValue + ww
                    if showSnap:
                        snapIndicator.left = snapValue - 2
                        snapIndicator.width = wl - snapValue + ww + 4
                        uiutil.GetChild(snapIndicator, 'sLeft').state = uiconst.UI_DISABLED
                if side == 'right':
                    if doSnap:
                        if wnd.IsResizeable():
                            wnd.width = snapValue - wl
                    if showSnap:
                        snapIndicator.width = snapValue - wl + 4
                        uiutil.GetChild(snapIndicator, 'sRight').state = uiconst.UI_DISABLED
                if side == 'top':
                    if doSnap:
                        wnd.top = snapValue
                        if wnd.IsResizeable():
                            wnd.height = wnd._fixedHeight or max(minH, wt - snapValue + wh)
                    if showSnap:
                        snapIndicator.top = snapValue - 2
                        snapIndicator.height = wt - snapValue + wh + 4
                        uiutil.GetChild(snapIndicator, 'sTop').state = uiconst.UI_DISABLED
                if side == 'bottom':
                    if doSnap:
                        if wnd.IsResizeable():
                            wnd.height = wnd._fixedHeight or max(minH, snapValue - wt)
                    if showSnap:
                        snapIndicator.height = snapValue - wt + 4
                        uiutil.GetChild(snapIndicator, 'sBottom').state = uiconst.UI_DISABLED
                checkMultipleSideSnap[wnd].append(side)

    def SetActive(self, *args):
        self.OnSetActive_(self)

    def HideSnapIndicator(self):
        snapIndicator = uiutil.FindChild(self.parent, 'snapIndicator')
        if snapIndicator is not None:
            snapIndicator.Close()

    def GetSnapIndicator(self):
        snapIndicator = uiutil.FindChild(self.parent, 'snapIndicator')
        if snapIndicator is None:
            snapIndicator = uicls.Container(parent=self.parent, color=(0.0, 1.0, 0.0, 1.0), align=uiconst.TOPLEFT, name='snapIndicator')
            for label, align, icon in [('sLeftTop', uiconst.TOPLEFT, 'ui_1_16_1'),
             ('sRightTop', uiconst.TOPRIGHT, 'ui_1_16_3'),
             ('sRightBottom', uiconst.BOTTOMRIGHT, 'ui_1_16_35'),
             ('sLeftBottom', uiconst.BOTTOMLEFT, 'ui_1_16_33'),
             ('sLeft', uiconst.CENTERLEFT, 'ui_1_16_17'),
             ('sTop', uiconst.CENTERTOP, 'ui_1_16_2'),
             ('sRight', uiconst.CENTERRIGHT, 'ui_1_16_19'),
             ('sBottom', uiconst.CENTERBOTTOM, 'ui_1_16_34')]:
                indicator = uicls.Icon(parent=snapIndicator, name=label, align=align, state=uiconst.UI_HIDDEN, icon=icon)

        return snapIndicator

    def IndicateStackable(self, over):
        if not over or not self.IsStackable():
            if self.sr.stackIndicator:
                s1, s2 = self.sr.stackIndicator
                s1.Close()
                s2.Close()
                self.sr.stackIndicator = None
            return
        if not self.sr.stackIndicator:
            s1 = uicls.Fill(parent=self, color=(0.0, 0.0, 0.0, 1.0), height=6, width=0, align=uiconst.TOPLEFT, idx=0)
            s2 = uicls.Fill(parent=self.parent, color=(0.0, 0.0, 0.0, 1.0), height=6, width=0, align=uiconst.ABSOLUTE, idx=1)
            self.sr.stackIndicator = (s1, s2)
        s1, s2 = self.sr.stackIndicator
        l, t, w, h = self.GetAbsolute()
        s1.width = w
        if isinstance(self, self.GetStackClass()):
            s1.top = 18
        else:
            s1.top = 0
        ol, ot, ow, oh = over.GetAbsolute()
        s2.left = ol
        s2.width = ow
        if isinstance(over, self.GetStackClass()):
            s2.top = ot + 18
        else:
            s2.top = ot

    def ClearStackIndication(self):
        self.IndicateStackable(None)

    def ShowSnapEdges_Moving(self, snapGroup, snapGrid, snapIndicator = None, doSnap = False):
        if snapGrid is None:
            return
        l, t, w, h = gl, gt, gw, gh = self.GetGroupAbsolute(snapGroup)
        snapdist = settings.char.windows.Get('snapdistance', 12)
        if not snapdist:
            self.HideSnapIndicator()
            return
        lSnap = None
        rSnap = None
        tSnap = None
        bSnap = None
        minLDist = 1000
        minRDist = 1000
        minTDist = 1000
        minBDist = 1000
        horizontal, vertical = snapGrid
        for hAxe in horizontal:
            tDist = abs(hAxe - t)
            bDist = abs(hAxe - (t + h))
            if tDist <= snapdist and tDist < minTDist:
                tSnap = hAxe
                minTDist = tDist
            elif bDist <= snapdist and bDist < minBDist:
                bSnap = hAxe
                minBDist = bDist

        for vAxe in vertical:
            lDist = abs(vAxe - l)
            rDist = abs(vAxe - (l + w))
            if lDist <= snapdist and lDist < minLDist:
                lSnap = vAxe
                minLDist = lDist
            elif rDist <= snapdist and rDist < minRDist:
                rSnap = vAxe
                minRDist = rDist

        if tSnap is not None:
            t = tSnap
            if bSnap is not None:
                h = bSnap - tSnap
        elif bSnap is not None:
            t = bSnap - h
        if lSnap is not None:
            l = lSnap
            if rSnap is not None:
                w = rSnap - lSnap
        elif rSnap is not None:
            l = rSnap - w
        if snapIndicator and not snapIndicator.destroyed:
            snapIndicator.width = w + 6
            snapIndicator.height = h + 6
            snapIndicator.left = l - 2
            snapIndicator.top = t - 2
            for each in snapIndicator.children:
                each.state = uiconst.UI_HIDDEN

            snapIndicator.SetOrder(1)
            if lSnap is not None:
                uiutil.GetChild(snapIndicator, 'sLeft').state = uiconst.UI_DISABLED
            if rSnap is not None:
                uiutil.GetChild(snapIndicator, 'sRight').state = uiconst.UI_DISABLED
            if tSnap is not None:
                uiutil.GetChild(snapIndicator, 'sTop').state = uiconst.UI_DISABLED
            if bSnap is not None:
                uiutil.GetChild(snapIndicator, 'sBottom').state = uiconst.UI_DISABLED
            snapIndicator.state = uiconst.UI_DISABLED
        leftOffset, rightOffset = self.GetSideOffset()
        cornerSnap = ''
        if tSnap in (0, 16):
            cornerSnap = 'top'
        elif bSnap in (uicore.desktop.height, uicore.desktop.height - 16):
            cornerSnap = 'bottom'
        if cornerSnap:
            if lSnap in (leftOffset, leftOffset + 16):
                cornerSnap = cornerSnap + 'left'
            elif rSnap in (uicore.desktop.width, uicore.desktop.width - 16):
                cornerSnap = cornerSnap + 'right'
        if doSnap:
            scaleX = float(w) / gw
            scaleY = float(h) / gh
            diffX = l - gl
            diffY = t - gt
            for wnd in snapGroup:
                wnd.left += diffX
                wnd.top += diffY
                if wnd.IsResizeable():
                    wnd.width = int(wnd.width * scaleX)
                    wnd.height = int(wnd.height * scaleY)

            for wnd in snapGroup:
                if wnd._fixedHeight and wnd.height != wnd._fixedHeight:
                    diff = wnd.height - wnd._fixedHeight
                    bottomAlignedWindows = wnd.FindConnectingWindows('bottom')
                    wnd.height -= diff
                    for each in bottomAlignedWindows[1:]:
                        each.top -= diff

                if wnd._fixedWidth and wnd.width != wnd._fixedWidth:
                    diff = wnd.width - wnd._fixedWidth
                    rightAlignedWindows = wnd.FindConnectingWindows('right')
                    wnd.width -= diff
                    for each in rightAlignedWindows[1:]:
                        each.left -= diff

    def FindWindowToStackTo(self):
        over = uicore.uilib.mouseOver
        if over is self:
            return None
        over = uiutil.GetWindowAbove(over)
        if not isinstance(over, uicls.WindowCore) or not over.IsStackable():
            self.ClearStackIndication()
            return None
        if over.InStack():
            over = over.sr.stack
        l, t, w, h = over.GetAbsolute()
        sl, st, sw, sh = self.GetAbsolute()
        isStack = isinstance(over, self.GetStackClass())
        pickSize = 32
        if isStack:
            pickSize += 18
        if (l < sl < l + w or l < sl + sw < l + w) and t <= st <= t + pickSize:
            self.IndicateStackable(over)
            return over
        self.ClearStackIndication()

    def IsStackable(self):
        if getattr(self, '_stackable', 1) and not self.IsLocked():
            shiftonly = settings.user.ui.Get('stackwndsonshift', 0)
            if shiftonly:
                return uicore.uilib.Key(uiconst.VK_SHIFT)
            return 1
        return 0

    def OnMouseUp(self, *args):
        self.ClearStackIndication()
        self.CleanupParent('snapIndicator')
        self.ShowHeaderButtons()
        uicore.uilib.UnclipCursor()
        self._dragging = False
        self._dragEnabled = False
        self._draginited = 0
        self.RegisterPositionAndSize()

    def OnDblClick(self, *args):
        if getattr(self, 'isDialog', False):
            return
        self.ToggleCollapse()

    def ToggleCollapse(self):
        if not self._collapseable:
            return
        self.ResetToggleState()
        if self.IsCollapsed():
            self.Expand()
        else:
            self.Collapse()

    def ToggleMinimize(self):
        if not self.IsMinimizable():
            return
        if self.IsMinimized():
            self.Maximize()
        elif self.InStack():
            if uicore.layer.main.children and uicore.layer.main.children[0] != self.GetStack():
                uicore.registry.SetFocus(self)
                self.GetStack().ShowWnd(self)
            elif self.GetStack().GetActiveWindow() != self:
                self.GetStack().ShowWnd(self)
            else:
                self.Minimize()
        elif uicore.layer.main.children and uicore.layer.main.children[0] != self:
            uicore.registry.SetFocus(self)
        else:
            self.Minimize()

    def ResetToggleState(self):
        uicore.registry.toggleState = None

    def GetCollapsedHeight(self):
        if self.sr.headerParent:
            return self.sr.headerParent.height
        return 18

    def GetHeaderHeight(self):
        if self.sr.headerParent:
            return self.sr.headerParent.height
        return 0

    def Collapse(self, *args, **kwds):
        if not self.parent or not self._collapseable or self.IsCollapsed():
            return
        if self.InStack():
            return self.sr.stack.Collapse()
        bottomAlignedWindows = self.FindConnectingWindows('bottom')
        allAlignedWindows = self.FindConnectingWindows()
        gl, gt, gw, gh = self.GetGroupAbsolute(allAlignedWindows)
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        ch = self.GetCollapsedHeight()
        heightDiff = self.height - ch
        self._SetCollapsed(True)
        self.LockHeight(ch)
        alignedToBottom = False
        alignedToTop = False
        pl, pt, pw, ph = self.parent.GetAbsolute()
        if gt in (0, 16):
            alignedToTop = True
        elif gt + gh in (ph, ph - 16):
            alignedToBottom = True
        if alignedToBottom:
            topAlignedWindows = self.FindConnectingWindows('top')
            for wnd in topAlignedWindows:
                wnd.top += heightDiff

        else:
            for wnd in bottomAlignedWindows:
                if wnd == self:
                    continue
                wnd.top -= heightDiff

        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if shift:
            affected = allAlignedWindows
            for each in affected:
                if each != self:
                    each.Collapse()

        if self.sr.headerLine:
            self.sr.headerLine.state = uiconst.UI_HIDDEN
        if self.sr.buttonParent:
            self.sr.buttonParent.state = uiconst.UI_HIDDEN
        self.sr.content.state = uiconst.UI_HIDDEN
        self.RefreshHeaderButtonsIfVisible()
        self.OnCollapsed(self)

    def Compact(self):
        self._SetCompact(True)

    def UnCompact(self):
        self._SetCompact(False)

    def HideButtons(self):
        if self.sr.buttonParent:
            self.sr.buttonParent.Hide()

    def ShowButtons(self):
        if self.sr.buttonParent:
            self.sr.buttonParent.Show()

    def Expand(self, *args):
        if not self.parent or not self.IsCollapsed():
            return
        if self.InStack():
            return self.sr.stack.Expand(*args)
        self.UnlockHeight()
        bottomAlignedWindows = self.FindConnectingWindows('bottom')
        gl, gt, gw, gh = self.GetGroupAbsolute(bottomAlignedWindows)
        pl, pt, pw, ph = self.parent.GetAbsolute()
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        alignedToBottom = False
        if gt + gh in (ph, ph - 16):
            alignedToBottom = True
        left, top, width, height, dw, dh = self.GetRegisteredPositionAndSize()
        height = max(height, self.GetMinHeight())
        heightDiff = height - self.height
        self._SetCollapsed(False)
        self.height = height
        if alignedToBottom:
            topAlignedWindows = self.FindConnectingWindows('top')
            for wnd in topAlignedWindows:
                wnd.top = max(0, wnd.top - heightDiff)

        else:
            for wnd in bottomAlignedWindows:
                if wnd == self:
                    continue
                wnd.top = min(wnd.top + heightDiff, uicore.desktop.height - wnd.height)

        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if shift:
            affected = self.FindConnectingWindows()
            for each in affected:
                if each != self:
                    each.Expand()

        if self.sr.headerLine:
            self.sr.headerLine.state = uiconst.UI_DISABLED
        if self.sr.buttonParent:
            self.sr.buttonParent.state = uiconst.UI_PICKCHILDREN
        self.sr.content.state = uiconst.UI_PICKCHILDREN
        self.RefreshHeaderButtonsIfVisible()
        self.OnExpanded(self)
        self.ValidateWindows()

    def ValidateWindows(self):
        d = uicore.desktop
        all = uicore.registry.GetValidWindows(getModals=1, floatingOnly=True)
        for wnd in all:
            if wnd.GetAlign() != uiconst.RELATIVE:
                continue
            wnd.left = max(-wnd.width + 64, min(d.width - 64, wnd.left))
            wnd.top = max(0, min(d.height - wnd.GetCollapsedHeight(), wnd.top))

    def CheckStack(self, drop):
        if not self.IsStackable():
            return
        if self.sr.modalParent is not None or drop.sr.modalParent is not None or drop == self:
            return
        if isinstance(self, uicls.WindowStack):
            if not isinstance(drop, uicls.WindowStack):
                self.InsertWnd(drop, 0, 1)
            else:
                for wnd in drop.GetWindows()[:]:
                    self.InsertWnd(wnd, 0, 1)

                drop.Close()
            return
        if self.state != uiconst.UI_HIDDEN:
            wnds = [(self, 0)]
            location = None
            kill = []
            if isinstance(drop, uicls.WindowStack):
                for wnd in drop.GetWindows():
                    wnds.append((wnd, wnd.state == uiconst.UI_NORMAL))

                kill.append(drop)
            else:
                wnds.append((drop, 1))
            self.Stack(wnds, kill)

    def CheckWndPos(self, i = 0):
        if self.parent is None or self.parent.destroyed or i == 10:
            return
        for each in self.parent.children:
            if each != self and each.state == uiconst.UI_NORMAL:
                if each.left == self.left and each.top == self.top:
                    self.left = self.left + POSOVERLAPSHIFT
                    self.top = self.top + POSOVERLAPSHIFT
                    if self.left + self.width > uicore.desktop.width:
                        self.left = uicore.desktop.width - self.width
                    if self.top + self.height > uicore.desktop.height:
                        self.top = uicore.desktop.height - self.height
                    self.CheckWndPos(i + 1)
                    break

    def Stack(self, wnds, kill, group = None, groupidx = None):
        stack = uicore.registry.GetStack(str(uthread.uniqueId()), self.GetStackClass())
        for _wnd in wnds:
            wnd, show = _wnd
            stack.InsertWnd(wnd, 1, show)
            stack.stack_starting = 0

        for each in kill:
            if each is not None and not each.destroyed:
                each.Close()

    def SetHeight(self, height):
        if self.GetAlign() == uiconst.RELATIVE and height != self.height:
            self.height = height

    def SetHeight_PushOrPullWindowsBelow(self, newHeight):
        if self.GetAlign() == uiconst.RELATIVE and newHeight != self.height:
            bottomAlignedWindows = self.FindConnectingWindows('bottom')
            heightDiff = newHeight - self.height
            self.height = newHeight
            for wnd in bottomAlignedWindows:
                if wnd == self:
                    continue
                wnd.top += heightDiff

    def GetMinWidth(self):
        if self._fixedWidth:
            return min(self._fixedWidth, self.minsize[0])
        w, h = self.GetMinSize()
        return max(w, self.minsize[0])

    def GetMinHeight(self):
        if self._fixedHeight:
            return min(self._fixedHeight, self.minsize[1])
        w, h = self.GetMinSize()
        return max(h, self.minsize[1])

    def GetMaxWidth(self):
        if self._fixedWidth:
            return self._fixedWidth
        return self.maxsize[0] or sys.maxint

    def GetMaxHeight(self):
        if self._fixedHeight:
            return self._fixedHeight
        return self.maxsize[1] or sys.maxint

    def GetClipRectModify(self, sides):
        l, t, w, h = self.GetAbsolute()
        mx = uicore.uilib.x
        my = uicore.uilib.y
        rl, rt, rr, rb = (0, 0, 0, 0)
        if 'right' in sides:
            rl = l + w - mx
        if 'left' in sides:
            rr = l - mx
        if 'bottom' in sides:
            rt = t + h - my
        if 'top' in sides:
            rb = t - my
        return (rl,
         rt,
         rr,
         rb)

    def CornersToSide(self, cs):
        sNames = ['left',
         'right',
         'top',
         'bottom']
        cMap = [(3, 2),
         (0, 1),
         (1, 0),
         (2, 3),
         (0, 3),
         (1, 2),
         (2, 1),
         (3, 0)]
        if cs in cMap:
            return sNames[cMap.index(cs) // 2]

    def FindConnectingWindows(self, fromSide = None, wnds = None, validWnds = None, getParallelSides = 0, fullSideOnly = 0):
        if validWnds is None:
            validWnds = self.GetOtherWindows(useMe=True, checkAlign=True)
        l, t, w, h = self.GetAbsolute()
        fromWndCorners = [(l, t),
         (l + w, t),
         (l + w, t + h),
         (l, t + h)]
        if fromSide == 'left':
            validCornerPairs = [(3, 2), (0, 1)]
            if getParallelSides:
                validCornerPairs += [(3, 0), (0, 3)]
        elif fromSide == 'right':
            validCornerPairs = [(1, 0), (2, 3)]
            if getParallelSides:
                validCornerPairs += [(1, 2), (2, 1)]
        elif fromSide == 'top':
            validCornerPairs = [(0, 3), (1, 2)]
            if getParallelSides:
                validCornerPairs += [(0, 1), (1, 0)]
        elif fromSide == 'bottom':
            validCornerPairs = [(2, 1), (3, 0)]
            if getParallelSides:
                validCornerPairs += [(3, 2), (2, 3)]
        else:
            validCornerPairs = [(3, 2),
             (0, 1),
             (1, 0),
             (2, 3),
             (0, 3),
             (1, 2),
             (2, 1),
             (3, 0)]
        wnds = wnds or []
        if self not in wnds:
            wnds.append(self)
        for wnd in validWnds:
            if wnd in wnds:
                continue
            wl, wt, ww, wh = wnd.GetAbsolute()
            wndCorners = ((wl, wt),
             (wl + ww, wt),
             (wl + ww, wt + wh),
             (wl, wt + wh))
            m = 0
            for c1, c2 in validCornerPairs:
                c1Pos = fromWndCorners[c1]
                c2Pos = wndCorners[c2]
                if c1Pos == c2Pos:
                    if not fullSideOnly or m == 1:
                        if getParallelSides:
                            wnd.FindConnectingWindows(None, wnds, validWnds, getParallelSides, fullSideOnly)
                        else:
                            wnd.FindConnectingWindows(fromSide, wnds, validWnds, getParallelSides, fullSideOnly)
                        break
                    m += 1

        return wnds

    def PrepareWindowsForMove(self, wnds):
        for each in wnds:
            l, t, w, h = each.GetAbsolute()
            each._grab = [uicore.uilib.x - l, uicore.uilib.y - t]
            each.preDragAbs = each.GetAbsolute()
            each.preDragCursorPos = (uicore.uilib.x, uicore.uilib.y)
            each.SetOrder(0)

    def CleanupParent(self, what):
        for each in self.parent.children[:]:
            if each.name == what:
                each.Close()

    def FindMinMaxScaling(self, sides):
        scaleH, scaleV, scaleAbove, followL, followR, followT, followB, all = self.sortedScaleWindows
        pl, pt, pw, ph = self.parent.GetAbsolute()
        myMinX = minX = 0
        myMaxX = maxX = pw
        myMinY = minY = 0
        myMaxY = maxY = ph
        for wnd in scaleH + [self]:
            spdl, spdt, spdw, spdh = wnd.preDragAbs
            wndMinWidth = wnd.GetMinWidth()
            wndMaxWidth = wnd.GetMaxWidth()
            if 'left' in sides:
                minX = max(minX, spdl + spdw - wndMaxWidth)
                maxX = min(maxX, spdl + spdw - wndMinWidth)
            elif 'right' in sides:
                minX = max(minX, spdl + wndMinWidth)
                maxX = min(maxX, spdl + wndMaxWidth)

        for wnd in scaleV + [self]:
            spdl, spdt, spdw, spdh = wnd.preDragAbs
            wndMinHeight = wnd.GetMinHeight()
            wndMaxHeight = wnd.GetMaxHeight()
            if 'top' in sides:
                minY = max(minY, spdt + spdh - wndMaxHeight)
                maxY = min(maxY, spdt + spdh - wndMinHeight)
            elif 'bottom' in sides:
                minY = max(minY, spdt + wndMinHeight)
                maxY = min(maxY, spdt + wndMaxHeight)

        for wnd in scaleAbove:
            spdl, spdt, spdw, spdh = wnd.preDragAbs
            wndMinHeight = wnd.GetMinHeight()
            wndMaxHeight = wnd.GetMaxHeight()
            minY = max(minY, spdt + wndMinHeight)
            maxY = min(maxY, spdt + wndMaxHeight)

        spdl, spdt, spdw, spdh = self.preDragAbs
        myMinWidth = self.GetMinWidth()
        myMinHeight = self.GetMinHeight()
        myMaxWidth = self.GetMaxWidth()
        myMaxHeight = self.GetMaxHeight()
        mx, my = self.preDragCursorPos
        if 'top' in sides:
            myMaxY = min(myMaxY, spdt + spdh - myMinHeight)
            myMinY = max(myMinY, spdt + spdh - myMaxHeight)
            for wnd in followT:
                pdl, pdt, pdw, pdh = wnd.preDragAbs
                minY = max(minY, spdt - pdt)

        elif 'bottom' in sides:
            myMinY = max(myMinY, spdt + myMinHeight)
            myMaxY = min(myMaxY, spdt + myMaxHeight)
            for wnd in followB:
                pdl, pdt, pdw, pdh = wnd.preDragAbs
                maxY = min(maxY, spdt + spdh + (ph - (pdt + pdh)))

        if 'left' in sides:
            myMaxX = min(myMaxX, spdl + spdw - myMinWidth)
            myMinX = max(myMinX, spdl + spdw - myMaxWidth)
            for wnd in followL:
                pdl, pdt, pdw, pdh = wnd.preDragAbs
                minX = max(minX, spdl - pdl)

        elif 'right' in sides:
            myMinX = max(myMinX, spdl + myMinWidth)
            myMaxX = min(myMaxX, spdl + myMaxWidth)
            for wnd in followR:
                pdl, pdt, pdw, pdh = wnd.preDragAbs
                maxX = min(maxX, spdl + spdw + (pw - (pdl + pdw)))

        return ((minX,
          minY,
          maxX,
          maxY), (myMinX,
          myMinY,
          myMaxX,
          myMaxY))

    def ModifyRect(self, sides):
        l, t, w, h = self.GetAbsolute()
        mx = uicore.uilib.x
        my = uicore.uilib.y
        rl, rt, rr, rb = (0, 0, 0, 0)
        rh = rv = 0
        if 'right' in sides:
            rh = l + w - mx
        elif 'left' in sides:
            rh = l - mx
        if 'bottom' in sides:
            rv = t + h - my
        elif 'top' in sides:
            rv = t - my
        return (int(rh),
         int(rv),
         int(rh),
         int(rv))

    @telemetry.ZONE_METHOD
    def UpdateClipCursor(self, rect, mrect):
        ml, mt, mr, mb = mrect
        rl, rt, rr, rb = rect
        uicore.uilib.ClipCursor(rl - ml, rt - mt, rr - mr, rb - mb)

    def GetSidesFromScalerName(self, sName):
        ret = []
        for s in ['Left',
         'Top',
         'Right',
         'Bottom']:
            if s in sName:
                ret.append(s.lower())

        return ret

    def StartScale(self, sender, btn, *args):
        if btn == uiconst.MOUSELEFT and self.IsResizeable():
            self.scaleSides = self.GetSidesFromScalerName(sender.name)
            self.sortedScaleWindows = self.SortScaleWindows(self.scaleSides)
            self.minmaxScale = self.FindMinMaxScaling(self.scaleSides)
            self.CreateSnapGrid(self.sortedScaleWindows[-1])
            self.OnStartScale_(self)
            self._scaling = True
            uthread.new(self.OnScale, sender)

    def SortScaleWindows(self, sides):
        wnds = []
        for side in sides:
            wnds += self.FindConnectingWindows(side, getParallelSides=1)

        self.PrepareWindowsForMove(wnds)
        ml, mt, mw, mh = self.GetAbsolute()
        scaleWidthMeH = []
        scaleWidthMeV = []
        onLeft = []
        onRight = []
        onBottom = []
        onTop = []
        all = [self]
        scaleAbove = []
        for wnd in wnds:
            if wnd == self or wnd in all:
                continue
            l, t, w, h = wnd.GetAbsolute()
            if l == ml and w == mw:
                scaleWidthMeH.append(wnd)
            elif l >= ml + mw:
                onRight.append(wnd)
            elif l + w <= ml:
                onLeft.append(wnd)
            elif 'right' in sides:
                onRight.append(wnd)
            elif 'left' in sides:
                onLeft.append(wnd)
            if t == mt and h == mh:
                scaleWidthMeV.append(wnd)
            elif t >= mt + mh:
                onBottom.append(wnd)
            elif t + h == mt and 'top' in sides:
                scaleAbove.append(wnd)
            elif t == mt and 'top' in sides:
                onTop.append(wnd)
            all.append(wnd)

        return (scaleWidthMeH,
         scaleWidthMeV,
         scaleAbove,
         onLeft,
         onRight,
         onTop,
         onBottom,
         all)

    @telemetry.ZONE_METHOD
    def OnScale(self, sender, *args):
        mRect = self.ModifyRect(self.scaleSides)
        while self._scaling and uicore.uilib.leftbtn and self and not self.destroyed:
            diffx = uicore.uilib.x - self.preDragCursorPos[0]
            diffy = uicore.uilib.y - self.preDragCursorPos[1]
            shift = uicore.uilib.Key(uiconst.VK_SHIFT)
            allMinMaxRect, myMinMaxRect = self.minmaxScale
            if shift:
                snapGrid = self.snapGrid[2]
                rect = allMinMaxRect
            else:
                snapGrid = self.snapGrid[1]
                rect = myMinMaxRect
            self.UpdateClipCursor(rect, mRect)
            if not shift:
                for wnd in self.sortedScaleWindows[-1]:
                    wpdl, wpdt, wpdw, wpdh = wnd.preDragAbs
                    wnd.left = wpdl
                    wnd.top = wpdt
                    wnd.width = wpdw
                    wnd.height = wpdh

                scaleH, scaleV, scaleAbove, followL, followR, followT, followB = ([],
                 [],
                 [],
                 [],
                 [],
                 [],
                 [])
            else:
                scaleH, scaleV, scaleAbove, followL, followR, followT, followB, all = self.sortedScaleWindows
            for side in self.scaleSides:
                if side in ('left', 'right') and self.GetMinWidth() != self.GetMaxWidth():
                    for wnd in scaleH + [self]:
                        wpdl, wpdt, wpdw, wpdh = wnd.preDragAbs
                        if side == 'left':
                            wnd.left = wpdl + diffx
                            if wnd.IsResizeable():
                                wnd.width = wnd._fixedWidth or wpdw - diffx
                        elif side == 'right':
                            if wnd.IsResizeable():
                                wnd.width = wnd._fixedWidth or wpdw + diffx

                    for wnd in [followR, followL][side == 'left']:
                        wpdl, wpdt, wpdw, wpdh = wnd.preDragAbs
                        wnd.left = wpdl + diffx

                if side in ('top', 'bottom') and self.GetMinHeight() != self.GetMaxHeight():
                    for wnd in scaleV + [self]:
                        wpdl, wpdt, wpdw, wpdh = wnd.preDragAbs
                        if side == 'top':
                            if wnd.IsResizeable():
                                wnd.height = wnd._fixedHeight or wpdh - diffy
                            wnd.top = wpdt + diffy
                        elif side == 'bottom':
                            if wnd.IsResizeable():
                                wnd.height = wnd._fixedHeight or wpdh + diffy

                    for wnd in [followB, followT][side == 'top']:
                        wpdl, wpdt, wpdw, wpdh = wnd.preDragAbs
                        wnd.top = wpdt + diffy

                    for wnd in scaleAbove:
                        wpdl, wpdt, wpdw, wpdh = wnd.preDragAbs
                        if wnd.IsResizeable():
                            wnd.height = wnd._fixedHeight or wpdh + diffy

            self.ShowSnapEdges_Scaling(snapGrid)
            self.OnScale_(self)
            uicls.Area._OnResize(self)
            blue.pyos.synchro.SleepWallclock(1)

    def EndScale(self, sender, *args):
        self.CleanupParent('snapIndicator')
        if not self.IsResizeable():
            return
        self._scaling = False
        uicore.uilib.UnclipCursor()
        if self.destroyed:
            return
        if self.snapGrid:
            snapGrid = self.snapGrid[1]
            self.ShowSnapEdges_Scaling(snapGrid, showSnap=False, doSnap=True)
        self.RegisterPositionAndSize()
        self.ShowHeaderButtons()
        self.OnEndScale_(self)

    def GetGroupAbsolute(self, group):
        return self.GetGroupRect(group, 1)

    def OnResize_(self, *args):
        pass

    def OnScale_(self, wnd, *args):
        pass

    def OnStartScale_(self, wnd, *args):
        pass

    def OnEndScale_(self, wnd, *args):
        pass

    def OnMouseDown_(self, what):
        pass

    def OnStartMinimize_(self, *args):
        pass

    def OnEndMinimize_(self, *args):
        pass

    def OnStartMaximize_(self, *args):
        pass

    def OnEndMaximize_(self, *args):
        pass

    def OnSetActive_(self, *args):
        pass

    def UpdateCaption_(self, *args):
        pass

    def OnCollapsed(self, wnd, *args):
        pass

    def OnExpanded(self, wnd, *args):
        pass

    def OnDragTick(self, *args):
        pass

    def GetIntersectingWindows(self):
        all = uicore.registry.GetWindows()
        ml, mt, mw, mh = self.GetAbsolute()
        intersecting = []
        for otherWindow in all:
            if otherWindow is self:
                continue
            if otherWindow.GetStack():
                continue
            if otherWindow.IsHidden():
                continue
            ol, ot, ow, oh = otherWindow.GetAbsolute()
            if not (ml <= ol < ml + mw or ml < ol + ow <= ml + mw or ml >= ol and ol + ow > ml + mw):
                continue
            if not (mt <= ot < mt + mh or mt < ot + oh <= mt + mh or mt >= ot and ot + oh > mt + mh):
                continue
            intersecting.append(otherWindow)

        return intersecting

    @classmethod
    def GetTopRight_TopOffset(cls):
        leftpush, rightpush = cls.GetSideOffset()
        cornerWnd = None
        for each in uicore.layer.main.children:
            if not isinstance(each, uicls.WindowCore) or each.state == uiconst.UI_HIDDEN:
                continue
            if each.left + each.width in (uicore.desktop.width - rightpush, uicore.desktop.width - rightpush - 16):
                if each.top in (0, 16):
                    cornerWnd = each
                    break

        if cornerWnd:
            bottomAlignedWindows = cornerWnd.FindConnectingWindows('bottom')
            if bottomAlignedWindows:
                groupRect = cls.GetGroupRect(bottomAlignedWindows)
                return groupRect[3]

    @classmethod
    def GetBottomLeft_TopOffset(cls):
        leftpush, rightpush = cls.GetSideOffset()
        cornerWnd = None
        for each in uicore.layer.main.children:
            if not isinstance(each, uicls.WindowCore) or each.state == uiconst.UI_HIDDEN:
                continue
            if each.left in (leftpush, leftpush + 16):
                if each.top + each.height in (uicore.desktop.height, uicore.desktop.height - 16):
                    cornerWnd = each
                    break

        if cornerWnd:
            topAlignedWindows = cornerWnd.FindConnectingWindows('top')
            if topAlignedWindows:
                groupRect = cls.GetGroupRect(topAlignedWindows)
                return groupRect[1]

    @classmethod
    def GetDesktopWindowLayout(cls):
        layout = {}
        doneVertical = []
        doneHorizontal = []
        d = uicore.desktop

        def AddToGroup(wnds, groupName):
            group = layout.get(groupName, [])
            for wnd in wnds:
                if groupName in ('topAligned', 'bottomAligned') and wnd not in doneVertical:
                    if groupName == 'topAligned':
                        group.append((wnd.top, wnd))
                    elif groupName == 'bottomAligned':
                        group.append((d.height - wnd.top, wnd))
                    doneVertical.append(wnd)
                elif groupName in ('leftAligned', 'rightAligned') and wnd not in doneHorizontal:
                    if groupName == 'leftAligned':
                        group.append((wnd.left, wnd))
                    elif groupName == 'rightAligned':
                        group.append((d.width - wnd.left, wnd))
                    doneHorizontal.append(wnd)

            layout[groupName] = group

        leftOffset, rightOffset = cls.GetSideOffset()
        windowsToAdjust = uicore.registry.GetValidWindows(getModals=True, floatingOnly=True, getHidden=True)
        for wnd in windowsToAdjust:
            wndGroup = wnd.FindConnectingWindows('top', fullSideOnly=True)[1:] + wnd.FindConnectingWindows('bottom', fullSideOnly=True)
            l, t, r, b = cls.GetBoundries(wndGroup)
            if t in (0, 16):
                AddToGroup(wndGroup, 'topAligned')
            elif b in (0, 16):
                AddToGroup(wndGroup, 'bottomAligned')
            if l in (0, leftOffset, leftOffset + 16):
                AddToGroup(wndGroup, 'leftAligned')
            elif r in (0, rightOffset, rightOffset + 16):
                AddToGroup(wndGroup, 'rightAligned')

        layout['proportionalHorizontal'] = []
        layout['proportionalVertical'] = []
        for wnd in windowsToAdjust:
            if wnd not in doneHorizontal:
                layout['proportionalHorizontal'].append((float(wnd.left + wnd.width / 2) / d.width, wnd))
            if wnd not in doneVertical:
                layout['proportionalVertical'].append((float(wnd.top + wnd.height / 2) / d.height, wnd))

        return layout

    @classmethod
    def LoadDesktopWindowLayout(cls, layout):
        for groupName, wndData in layout.iteritems():
            for offset, wnd in wndData:
                if groupName == 'topAligned':
                    wnd.top = offset
                elif groupName == 'bottomAligned':
                    wnd.top = uicore.desktop.height - offset
                elif groupName == 'leftAligned':
                    wnd.left = offset
                elif groupName == 'rightAligned':
                    wnd.left = uicore.desktop.width - offset
                elif groupName == 'proportionalHorizontal':
                    wnd.left = max(0, min(uicore.desktop.width - wnd.width, int(offset * uicore.desktop.width) - wnd.width / 2))
                elif groupName == 'proportionalVertical':
                    wnd.top = max(0, min(uicore.desktop.height - wnd.height, int(offset * uicore.desktop.height) - wnd.height / 2))

    @classmethod
    def GetIfOpen(cls, windowID = None):
        if windowID:
            checkForWindowID = windowID
        else:
            checkForWindowID = cls.default_windowID
        if checkForWindowID:
            wnd = uicore.registry.GetWindow(checkForWindowID)
            return wnd

    @classmethod
    def CloseIfOpen(cls, windowID = None):
        wnd = cls.GetIfOpen(windowID)
        if wnd:
            wnd.Close()

    @classmethod
    def Open(cls, *args, **kwds):
        wnd = cls.GetIfOpen(windowID=kwds.get('windowID', None))
        if wnd:
            wnd.Maximize()
            return wnd
        newWindow = cls(**kwds)
        return newWindow

    @classmethod
    def ToggleOpenClose(cls, *args, **kwds):
        wnd = cls.GetIfOpen(windowID=kwds.get('windowID', None))
        if wnd:
            if wnd.IsMinimized():
                wnd.Maximize()
                return wnd
            wnd.CloseByUser()
        else:
            return cls.Open(*args, **kwds)

    @classmethod
    def IsOpen(cls, windowID = None):
        wnd = cls.GetIfOpen(windowID)
        return bool(wnd)

    @classmethod
    def GetRegisteredOrDefaultStackID(cls, windowID = None):
        windowID = windowID or cls.default_windowID
        if windowID:
            all = settings.char.windows.Get('stacksWindows', {})
            if windowID in all:
                return all[windowID]
            return all.get(windowID, cls.default_stackID)

    def GetRegisteredPositionAndSize(self):
        return self.GetRegisteredPositionAndSizeByClass(self.windowID)

    @classmethod
    def GetRegisteredPositionAndSizeByClass(cls, windowID = None):
        windowID = windowID or cls.default_windowID
        if type(windowID) == tuple:
            windowID, subWindowID = windowID
        all = settings.char.windows.Get('windowSizesAndPositions_1', {})
        usingDefault = 1
        if windowID and windowID in all:
            left, top, width, height, cdw, cdh = all[windowID]
            usingDefault = 0
        else:
            cdw, cdh = uicore.desktop.width, uicore.desktop.height
        if usingDefault:
            left, top, width, height = cls.GetDefaultSizeAndPosition()
            pushleft = cls.GetDefaultLeftOffset(width=width, align=uiconst.CENTER, left=left)
            if pushleft < 0:
                left = max(0, left + pushleft)
            elif pushleft > 0:
                left = min(left + pushleft, uicore.desktop.width - width)
        dw, dh = uicore.desktop.width, uicore.desktop.height
        if cdw != dw:
            wDiff = dw - cdw
            if left + width in (cdw, cdw - 16):
                left += wDiff
            elif left not in (0, 16):
                oldCenterX = (cdw - width) / 2
                xPortion = oldCenterX / float(cdw)
                newCenterX = int(xPortion * dw)
                cxDiff = newCenterX - oldCenterX
                left += cxDiff
        if cdh != dh:
            hDiff = dh - cdh
            if top in (0, 16):
                pass
            elif top + height in (cdh, cdh - 16):
                top += hDiff
            else:
                oldCenterY = (cdh - height) / 2
                yPortion = oldCenterY / float(cdh)
                newCenterY = int(yPortion * dh)
                cyDiff = newCenterY - oldCenterY
                top += cyDiff
        return (left,
         top,
         width,
         height,
         dw,
         dh)

    @classmethod
    def GetBoundries(cls, wnds, dw = None, dh = None):
        d = uicore.desktop
        dw = dw or d.width
        dh = dh or d.height
        l, t, r, b = cls.GetGroupRect(wnds)
        return (l,
         t,
         dw - r,
         dh - b)

    @classmethod
    def GetGroupRect(cls, group, getAbsolute = 0):
        if not len(group):
            return (0, 0, 0, 0)
        l, t, w, h = group[0].GetAbsolute()
        r = l + w
        b = t + h
        for wnd in group[1:]:
            wl, wt, ww, wh = wnd.GetAbsolute()
            l = min(l, wl)
            t = min(t, wt)
            r = max(r, wl + ww)
            b = max(b, wt + wh)

        if getAbsolute:
            return (l,
             t,
             r - l,
             b - t)
        return (l,
         t,
         r,
         b)

    @classmethod
    def GetDefaultSizeAndPosition(cls):
        dw = uicore.desktop.width
        dh = uicore.desktop.height
        if callable(cls.default_width):
            width = cls.default_width()
        else:
            width = cls.default_width
        if callable(cls.default_height):
            height = cls.default_height()
        else:
            height = cls.default_height
        if cls.default_left == '__center__':
            l = (dw - width) / 2
        elif cls.default_left == '__right__':
            l = dw - width
        elif callable(cls.default_left):
            l = cls.default_left()
        else:
            l = cls.default_left
        if cls.default_top == '__center__':
            t = (dh - height) / 2
        elif cls.default_top == '__bottom__':
            t = dh - height
        elif callable(cls.default_top):
            t = cls.default_top()
        else:
            t = cls.default_top
        return (l,
         t,
         width,
         height)

    @classmethod
    def GetDefaultLeftOffset(cls, *args, **kw):
        return 0

    @classmethod
    def GetSettingsVersion(cls):
        return 'CORE'

    @classmethod
    def ValidateSettings(cls):
        version = cls.GetSettingsVersion()
        log.LogInfo('Validate Window Settings, user:', session.userid, 'char:', session.charid)
        if not settings.char.windows.Get('__usercopy__', False):
            oldUserSettings = settings.user.windows.GetValues()
            log.LogInfo('CONVERTING SETTINGS FROM USER TO CHAR', session.userid, session.charid, 'settings:', oldUserSettings.keys())
            for settingKey in oldUserSettings.keys():
                oldValue = settings.user.windows.Get(settingKey)
                settings.char.windows.Set(settingKey, oldValue)

            settings.char.windows.Set('__usercopy__', True)
        if settings.char.windows.Get('__version__', None) != version:
            cls.ResetAllWindowSettings()

    @classmethod
    def ResetAllWindowSettings(cls):
        settings.char.Remove('windows')
        version = cls.GetSettingsVersion()
        log.LogInfo('Starting new window settings with', version, 'as version')
        settings.char.windows.Set('__version__', version)
        settings.char.windows.Set('__usercopy__', True)


exports = {'uicls.WindowCoreReady': True}
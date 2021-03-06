#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/control/hint.py
import uicls
import uiconst
import uiutil
import types
import blue
import log
import mathUtil
import uthread

class HintCore(uicls.Container):
    __guid__ = 'uicls.HintCore'
    default_fontsize = 10
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.opacity = 0.0
        self.SetSize(128, 16)
        self.Prepare_()

    def Prepare_(self):
        self.sr.textobj = uicls.Label(parent=self, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, pos=(8, 3, 200, 0), letterspace=1, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize)
        self.sr.underlay = uicls.Frame(parent=self, name='__underlay', frameConst=uiconst.FRAME_FILLED_CORNER0, color=(0.0, 0.0, 0.0, 1.0))

    def Prepare_HintStr_(self, hint):
        return hint

    def LoadHintFromItem(self, item, force):
        if item is None or uicore.uilib.leftbtn:
            self.FadeOpacity(0.0)
            self._lastHintInfo = None
            return
        hint = None
        if getattr(item, 'GetHint', None) is not None:
            hint = item.GetHint()
        hint = hint or getattr(item, 'hint', None)
        if hint is None and getattr(item, 'sr', None):
            hint = item.sr.Get('hint', None)
        if item.auxiliaryHint:
            if hint:
                hint += '<br>' + item.auxiliaryHint
            else:
                hint = item.auxiliaryHint
        if not hint:
            self.FadeOpacity(0.0)
            self._lastHintInfo = None
            return
        lastHint = getattr(self, '_lastHintInfo', None)
        if not lastHint or lastHint != (id(item), hint):
            self._lastHintInfo = (id(item), hint)
            uthread.worker('UICoreHint::LoadHintFromItem', self._LoadHintFromItemThread, item, hint)

    def _LoadHintFromItemThread(self, item, hint):
        if self.opacity == 0.0:
            blue.pyos.synchro.SleepWallclock(getattr(item, 'hintDelay', 100))
        else:
            blue.pyos.synchro.Yield()
        if self.destroyed:
            return
        mouseOver = uicore.uilib.mouseOver
        if mouseOver is not item:
            self.FadeOpacity(0.0)
            self._lastHintInfo = None
            return
        if hasattr(item, 'GetHintPosition'):
            hintAbLeft, hintAbTop, hintAbRight, hintAbBottom = item.GetHintPosition()
        else:
            hintAbLeft = getattr(item, 'hintAbLeft', None)
            hintAbRight = getattr(item, 'hintAbRight', None)
            hintAbTop = getattr(item, 'hintAbTop', None)
            hintAbBottom = getattr(item, 'hintAbBottom', None)
        self.LoadHint(hint, hintAbLeft, hintAbRight, hintAbTop, hintAbBottom)

    def LoadHint(self, hint = None, abLeft = None, abRight = None, abTop = None, abBottom = None):
        if self.destroyed:
            return
        if hint and not isinstance(hint, (str, unicode)):
            log.LogWarn('ShowHint only supports strings as hint', hint)
            return
        if not hint or self.sr.textobj is None:
            self.FadeOpacity(0.0)
            self._lastHintInfo = None
            return
        to = self.sr.textobj
        to.busy = 1
        hint = hint.replace('\t', '    ').replace('<t>', '    ')
        if bool(hint != to.text):
            to.width = 200
            to.height = 0
            to.busy = 0
            to.text = hint
            self.width = max(56, to.textwidth + to.left * 2)
            self.height = max(14, to.textheight + to.top) + 2
        pw, ph = self.parent.GetAbsoluteSize()
        if abRight:
            self.left = abRight - self.width
        else:
            self.left = abLeft or uicore.uilib.x + 8
        if abBottom:
            self.top = abBottom - self.height
        else:
            self.top = abTop or uicore.uilib.y - self.height - 8
        self.left = max(0, min(self.left, pw - self.width))
        self.top = max(0, min(self.top, ph - self.height))
        self.FadeOpacity(1.0)
        self.state = uiconst.UI_DISABLED

    def FadeOpacity(self, toOpacity):
        if toOpacity == getattr(self, '_settingOpacity', None):
            return
        self._newOpacity = toOpacity
        self._settingOpacity = toOpacity
        uthread.worker('UICoreHint::FadeOpacity', self.FadeOpacityThread, toOpacity)

    def FadeOpacityThread(self, toOpacity):
        self._newOpacity = None
        ndt = 0.0
        start = blue.os.GetWallclockTime()
        startOpacity = self.opacity
        while ndt != 1.0:
            ndt = min(float(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime())) / float(250.0), 1.0)
            self.opacity = min(1.0, max(0.0, mathUtil.Lerp(startOpacity, toOpacity, ndt)))
            if toOpacity == 1.0:
                self.Show()
            blue.pyos.synchro.Yield()
            if self._newOpacity:
                return

        if toOpacity == 0.0:
            self.Hide()
#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/util/logUtil.py
import util
import log
import sys

class LogMixin():

    def __init__(self, logChannel = None, bindObject = None):
        logChannelName = self.GetLogChannelName(logChannel, bindObject)
        self.__logname__ = self.GetLogName(logChannelName)
        self.logChannel = log.GetChannel(logChannelName)
        self.LoadPrefs()
        self.logContexts = {}
        for each in ('Info', 'Notice', 'Warn', 'Error'):
            self.logContexts[each] = 'Logging::' + each

    def GetLogChannelName(self, logChannelName = None, bindObject = None):
        if type(logChannelName) not in [str, type(None)]:
            raise Exception('logChannelName must be a string!')
        if logChannelName and bindObject:
            raise Exception('Conflicting log channel, provide logChannelName or bindObject, not both')
        bindguid = getattr(bindObject, '__guid__', None)
        bindLogName = getattr(bindObject, '__logname__', None)
        selfguid = getattr(self, '__guid__', None)
        return logChannelName or bindguid or bindLogName or selfguid or 'nonsvc.General'

    def GetLogName(self, logChannelName):
        tokens = logChannelName.split('.')
        if len(tokens) == 1:
            return tokens[0]
        else:
            return tokens[1]

    def ArrangeArguments(self, *args, **keywords):
        self.DeprecateKeywords(**keywords)
        argsList = []
        prefix = self.GetLogPrefix()
        if prefix:
            argsList.append(prefix)
        for item in args:
            argsList.append(item)

        return argsList

    def DeprecateKeywords(self, **keywords):
        if len(keywords):
            self.LogError('ERROR: keyword arguements passed into a log function')
            log.LogTraceback()

    def GetLogPrefix(self):
        return None

    def DudLogger(self, *args, **keywords):
        pass

    def LogMethodCall(self, *args, **keywords):
        if not prefs.GetValue('logMethodCalls', boot.role != 'client'):
            return
        argsList = self.ArrangeArguments(*args, **keywords)
        logChannel = log.methodcalls
        if getattr(self, 'isLogInfo', 0) and self.logChannel.IsLogChannelOpen(log.LGINFO):
            try:
                if len(argsList) == 1:
                    s = strx(argsList[0])
                else:
                    s = ' '.join(map(strx, argsList))
                logChannel.Log(s, log.LGINFO, 1, force=True)
            except TypeError:
                logChannel.Log('[X]'.join(map(strx, argsList)).replace('\x00', '\\0'), log.LGINFO, 1, force=True)
                sys.exc_clear()
            except UnicodeEncodeError:
                logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList))), log.LGINFO, 1, force=True)
                sys.exc_clear()

    def LogInfo(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if getattr(self, 'isLogInfo', 0) and self.logChannel.IsLogChannelOpen(log.LGINFO):
            try:
                if len(argsList) == 1:
                    s = strx(argsList[0])
                else:
                    s = ' '.join(map(strx, argsList))
                self.logChannel.Log(s, log.LGINFO, 1, force=True)
            except TypeError:
                self.logChannel.Log('[X]'.join(map(strx, argsList)).replace('\x00', '\\0'), log.LGINFO, 1, force=True)
                sys.exc_clear()
            except UnicodeEncodeError:
                self.logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList))), log.LGINFO, 1, force=True)
                sys.exc_clear()

    def LogWarn(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if self.isLogWarning and self.logChannel.IsLogChannelOpen(log.LGWARN) or charsession and not boot.role == 'client':
            try:
                if len(argsList) == 1:
                    s = strx(argsList[0])
                else:
                    s = ' '.join(map(strx, argsList))
                if self.logChannel.IsOpen(log.LGWARN):
                    self.logChannel.Log(s, log.LGWARN, 1, force=True)
                for x in util.LineWrap(s, 10):
                    if charsession and not boot.role == 'client':
                        charsession.LogSessionHistory(x, None, 1)

            except TypeError:
                sys.exc_clear()
                x = '[X]'.join(map(strx, argsList)).replace('\x00', '\\0')
                if self.logChannel.IsOpen(log.LGWARN):
                    self.logChannel.Log(x, log.LGWARN, 1, force=True)
                if charsession and not boot.role == 'client':
                    charsession.LogSessionHistory(x, None, 1)
            except UnicodeEncodeError:
                sys.exc_clear()
                x = '[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList)))
                if self.logChannel.IsOpen(log.LGWARN):
                    self.logChannel.Log(x, log.LGWARN, 1, force=True)
                if charsession and not boot.role == 'client':
                    charsession.LogSessionHistory(x, None, 1)

    def LogError(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if self.logChannel.IsOpen(log.LGERR) or charsession:
            try:
                if len(argsList) == 1:
                    s = strx(argsList[0])
                else:
                    s = ' '.join(map(strx, argsList))
                if self.logChannel.IsOpen(log.LGERR):
                    self.logChannel.Log(s, log.LGERR, 1)
                for x in util.LineWrap(s, 40):
                    if charsession:
                        charsession.LogSessionHistory(x, None, 1)

            except TypeError:
                sys.exc_clear()
                x = '[X]'.join(map(strx, argsList)).replace('\x00', '\\0')
                if self.logChannel.IsOpen(log.LGERR):
                    self.logChannel.Log(x, log.LGERR, 1)
                if charsession:
                    charsession.LogSessionHistory(x, None, 1)
            except UnicodeEncodeError:
                sys.exc_clear()
                x = '[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList)))
                if self.logChannel.IsOpen(log.LGERR):
                    self.logChannel.Log(x, log.LGERR, 1)
                if charsession and not boot.role == 'client':
                    charsession.LogSessionHistory(x, None, 1)

    def LogNotice(self, *args, **keywords):
        argsList = self.ArrangeArguments(*args, **keywords)
        if getattr(self, 'isLogInfo', 0) and self.logChannel.IsLogChannelOpen(log.LGNOTICE):
            try:
                if len(argsList) == 1:
                    s = strx(argsList[0])
                else:
                    s = ' '.join(map(strx, argsList))
                self.logChannel.Log(s, log.LGNOTICE, 1, force=True)
            except TypeError:
                self.logChannel.Log('[X]'.join(map(strx, argsList)).replace('\x00', '\\0'), log.LGNOTICE, 1, force=True)
                sys.exc_clear()
            except UnicodeEncodeError:
                self.logChannel.Log('[U]'.join(map(lambda x: x.encode('ascii', 'replace'), map(unicode, argsList))), log.LGNOTICE, 1, force=True)
                sys.exc_clear()

    def LoadPrefs(self):
        self.isLogInfo = bool(prefs.GetValue('logInfo', 1))
        self.isLogWarning = bool(prefs.GetValue('logWarning', 1))
        self.isLogNotice = bool(prefs.GetValue('logNotice', 1))

    def SetLogInfo(self, b):
        if not b and self.isLogInfo:
            self.LogInfo('*** LogInfo stopped for ', self.__guid__)
        old = self.isLogInfo
        self.isLogInfo = b
        if b and not old:
            self.LogInfo('*** LogInfo started for ', self.__guid__)

    def SetLogNotice(self, b):
        if not b and self.isLogNotice:
            self.LogInfo('*** LogNotice stopped for ', self.__guid__)
        old = self.isLogNotice
        self.isLogNotice = b
        if b and not old:
            self.LogInfo('*** LogNotice started for ', self.__guid__)

    def SetLogWarning(self, b):
        if not b and self.isLogWarning:
            self.LogWarn('*** LogWarn stopped for ', self.__guid__)
        old = self.isLogWarning
        self.isLogWarning = b
        if b and not old:
            self.LogWarn('*** LogWarn started for ', self.__guid__)


def _Log(severity, what):
    try:
        s = ' '.join(map(str, what))
    except UnicodeEncodeError:

        def conv(what):
            if isinstance(what, unicode):
                return what.encode('ascii', 'replace')
            return str(what)

        s = ' '.join(map(conv, what))

    log.general.Log(s.replace('\x00', '\\0'), severity)


def LogInfo(*what):
    _Log(log.LGINFO, what)


def LogNotice(*what):
    _Log(log.LGNOTICE, what)


def LogWarn(*what):
    _Log(log.LGWARN, what)


def LogError(*what):
    _Log(log.LGERR, what)


exports = util.AutoExports('log', locals())